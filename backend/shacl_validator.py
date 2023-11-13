#!/usr/bin/env python3

import logging
import re
from itertools import pairwise

import fire
import markdown
from bs4 import BeautifulSoup
from github import Github, UnknownObjectException
from github.Repository import Repository
from packaging import version
from packaging.version import Version
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

types = Namespace("https://example.org/repo/project-types/")
props = Namespace("https://example.org/repo/props/")


def get_project_type_specifications():
    with open("data/shacl/project_shapes.ttl") as raw_shapes_graph:

        raw_shapes_graph = list(raw_shapes_graph)

        type_spec_indices = []

        for index, line in enumerate(raw_shapes_graph):
            if line.startswith("types:"):
                current_type = line.replace("\n", "").strip()
                first_index = index + 2

            if (" ." in line) & ("@prefix" not in line):
                last_index = index + 1
                type_spec_indices.append((current_type, first_index, last_index))

    return process_project_types_for_display(raw_shapes_graph, type_spec_indices)


def process_project_types_for_display(raw_shapes_graph, type_spec_indices):
    project_type_specifications = {}
    for project_type, first_index, last_index in type_spec_indices:
        spec_block = "".join(raw_shapes_graph[first_index:last_index])

        spec_block = spec_block.replace("\t", "")
        spec_block = spec_block.replace("propertyShapes:", "")
        spec_block = spec_block.replace("nodeShapes:", "")
        spec_block = re.sub(r"sh:description\n?\s+\".*[;.]", "", spec_block)

        split_by_comments = spec_block.split("# ")

        # If there are comments on this project type, split based on these.
        if len(split_by_comments) > 1:
            specs = [spec.replace("sh:node ", "→ ") for spec in split_by_comments]
            specs = [spec.replace("sh:property ", "→ ") for spec in specs]
        else:
            specs = re.split(r"sh:property\s+|sh:node\s+", spec_block)

        specs = [spec.strip().removesuffix(";").strip() for spec in specs]
        specs = [spec.strip().removesuffix(".").strip() for spec in specs]

        project_type_specifications[project_type.removeprefix("types:")] = specs[1:]  # At index 0 of specs is "".

    return project_type_specifications


def create_project_type_representation() -> Graph:
    # Here, "graph merging" is used (https://rdflib.readthedocs.io/en/stable/merging.html).
    graph = Graph()
    graph.parse("./data/shacl/property_shapes.ttl")
    graph.parse("./data/shacl/node_shapes.ttl")
    graph.parse("./data/shacl/project_shapes.ttl")

    return graph


def get_requirements_list_for_repository_representation(graph: Graph, expected_type: str) -> list[str]:
    project_type_node = URIRef("https://example.org/repo/project-types/" + expected_type)
    predicate = URIRef("http://www.w3.org/ns/shacl#description")

    # https://rdflib.readthedocs.io/en/stable/intro_to_graphs.html#graph-methods-for-accessing-triples
    # Tries to get the value of "sh:description" of the project type. If there are multiple ones, an error is raised.
    description_literal = graph.value(subject=project_type_node, predicate=predicate, object=None, any=False)
    if not description_literal:
        raise ValueError("Project type '" + expected_type + "' is missing the mandatory triple with sh:description.")

    requirements_str = description_literal.__str__().removeprefix(
        "The following repository properties are required to validate this project type:")
    requirements_list = requirements_str.split(",")
    requirements_list = [requirement.strip() for requirement in requirements_list]
    requirements_list[-1] = requirements_list[-1].removesuffix(".")

    return requirements_list


def create_repository_representation(requirements_list: list[str], access_token: str = "", repo_name: str = "",
                                     expected_type: str = "") -> Graph:
    graph = Graph()
    github = Github(access_token) if access_token else Github()

    # get repo
    repo = github.get_repo(repo_name)
    repo_entity = URIRef(repo.html_url)
    graph.add((repo_entity, RDF.type, types[expected_type]))

    return add_required_properties_to_graph(graph, repo_entity, repo, requirements_list)


def add_required_properties_to_graph(graph: Graph, repo_entity: URIRef, repo: Repository,
                                     requirements_list: list[str]) -> Graph:
    requirements_function_mapping = {
        "Branches": include_branches,
        "DefaultBranch": include_default_branch,
        "DefaultBranchIncludingRootDirectoryFiles": include_default_branch_with_root_directory_files,
        "Description": include_description,
        "Homepage": include_homepage,
        "Issues": include_issues,
        "License": include_license,
        "MainLanguage": include_main_language,
        "ReadmeIncludingSections": include_readme_with_sections,
        "ReadmeIncludingCheckForDoi": include_readme_with_check_for_doi,
        "ReadmeIncludingSectionsAndCheckForDoi": include_readme_with_sections_and_check_for_doi,
        "Releases": include_releases,
        "ReleasesIncludingIncrementCheck": include_releases_with_increment_check,
        "Topics": include_topics,
        "Visibility": include_visibility
    }

    for requirement in requirements_list:
        if not requirements_function_mapping[requirement]:
            logging.exception(f"No function found for the requirement: {requirement}")
            continue

        # Manipulates the graph in-place
        requirements_function_mapping[requirement](graph, repo_entity, repo)

    return graph


def include_visibility(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    graph.add((repo_entity, props["is_private"], Literal(repo.private)))


def include_topics(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    topic_list = repo.get_topics()
    if topic_list:
        for topic in topic_list:
            graph.add((repo_entity, props["has_topic"], Literal(topic)))


def include_description(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    if repo.description:
        graph.add((repo_entity, props["has_description"], Literal(repo.description)))


def include_homepage(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    if repo.homepage:
        graph.add((repo_entity, props["has_homepage"], Literal(repo.homepage)))


def include_main_language(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    if repo.language:
        graph.add((repo_entity, props["has_main_language"], Literal(repo.language)))


def include_releases(graph: Graph, repo_entity: URIRef, repo: Repository,
                     check_version_increment: bool = False) -> None:
    release_list = repo.get_releases()
    if not release_list:
        return

    for release in release_list:
        release_entity = URIRef(release.html_url)
        graph.add((release_entity, props["has_tag_name"], Literal(release.tag_name)))
        graph.add((repo_entity, props["has_release"], release_entity))

    if not check_version_increment:
        return
    sorted_version_list = []
    try:
        # adapted from https://stackoverflow.com/a/11887885
        version_list = [version.parse(release.tag_name.removeprefix("v")) for release in release_list]
        sorted_version_list = sorted(version_list)
    except ValueError:
        graph.add((repo_entity, props["versions_have_valid_increment"], Literal("false")))

    if sorted_version_list:
        versions_have_valid_increment = True
        for pair in pairwise(sorted_version_list):
            if not pair_has_valid_version_increment(pair):
                versions_have_valid_increment = False
                break

        graph.add((repo_entity, props["versions_have_valid_increment"], Literal(versions_have_valid_increment)))


def include_releases_with_increment_check(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    return include_releases(graph, repo_entity, repo, check_version_increment=True)


def pair_has_valid_version_increment(pair: tuple[Version, Version]) -> bool:
    # If the first number (major) is increased, the second (minor) and third (micro) must be set to zero.
    if (pair[0].major < pair[1].major) & (pair[1].minor == 0) & (pair[1].micro == 0):
        return True

    # If minor in increased, micro must be set to zero.
    if (pair[0].major == pair[1].major) & (pair[0].minor < pair[1].minor) & (pair[1].micro == 0):
        return True

    # If micro is increased, major and minor must be unchanged.
    if (pair[0].major == pair[1].major) & (pair[0].minor == pair[1].minor) & (pair[0].micro < pair[1].micro):
        return True

    # If major, minor and macro are the same in both versions, the versions have to differ in the suffix.
    if (pair[0].major == pair[1].major) & (pair[0].minor == pair[1].minor) & (pair[0].micro == pair[1].micro) & (
            pair[0] != pair[1]):
        return True

    return False


def include_branches(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    branch_list = repo.get_branches()
    if branch_list:
        for branch in branch_list:
            branch_entity = URIRef(f"{repo.html_url}/tree/{branch.name}")
            graph.add((branch_entity, props["has_name"], Literal(branch.name)))
            graph.add((repo_entity, props["has_branch"], branch_entity))


def include_default_branch(graph: Graph, repo_entity: URIRef, repo: Repository,
                           include_root_directory_files: bool = False) -> None:
    default_branch_name = repo.default_branch
    if not default_branch_name:
        return

    branch_entity = URIRef(f"{repo.html_url}/tree/{default_branch_name}")
    graph.add((branch_entity, props["has_name"], Literal(default_branch_name)))
    graph.add((repo_entity, props["has_default_branch"], branch_entity))

    if not include_root_directory_files:
        return

    git_tree = repo.get_git_tree(default_branch_name)
    for item in git_tree.tree:
        if item.type == "blob":
            graph.add((branch_entity, props["has_file_in_root_directory"], Literal(item.path)))


def include_default_branch_with_root_directory_files(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    return include_default_branch(graph, repo_entity, repo, include_root_directory_files=True)


def include_issues(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    issue_list = repo.get_issues()
    if issue_list:
        for issue in issue_list:
            issue_entity = URIRef(issue.html_url)
            graph.add((issue_entity, props["has_state"], Literal(issue.state)))
            graph.add((repo_entity, props["has_issue"], issue_entity))


def include_license(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    try:
        license_data = repo.get_license()
        if license_data:
            graph.add((repo_entity, props["has_license"], Literal(license_data.license.name)))
    except UnknownObjectException as e:
        logging.exception(f"No license could be retrieved due to: {e}")


def include_readme(graph: Graph, repo_entity: URIRef, repo: Repository, include_sections: bool = False,
                   include_check_for_doi: bool = False) -> None:
    try:
        readme = repo.get_readme()
    except UnknownObjectException as e:
        logging.exception(f"No README file could be retrieved due to: {e}")
        return

    if not readme:
        return

    readme_entity = URIRef(readme.html_url)
    graph.add((repo_entity, props["has_readme"], readme_entity))

    if not (include_sections or include_check_for_doi):
        return

    md = markdown.Markdown()
    html = md.convert(readme.decoded_content.decode())
    soup = BeautifulSoup(html, "html.parser")

    if include_sections:
        heading_tags = ["h" + str(ctr) for ctr in range(1, 7)]
        headings_elems = [soup.find_all(tag)
                          for tag in heading_tags if soup.find_all(tag)]
        headings_elems = [
            item for sublist in headings_elems for item in sublist]
        headings = [item.text for item in headings_elems]

        for heading in headings:
            graph.add((readme_entity, props["has_section"], Literal(heading)))

    if include_check_for_doi:
        # Check whether there is at least one DOI in the README file (as text or link href).
        # Regex adapted from https://www.crossref.org/blog/dois-and-matching-regular-expressions/
        doi_pattern = re.compile(r"https://doi\.org/10\.\d{4,}/[-._;()/:A-Z0-9]+")
        if soup.find_all(string=doi_pattern) or soup.find_all(href=doi_pattern):
            graph.add((readme_entity, props["contains_doi"], Literal("true")))
        else:
            graph.add((readme_entity, props["contains_doi"], Literal("false")))


def include_readme_with_sections(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    return include_readme(graph, repo_entity, repo, include_sections=True)


def include_readme_with_check_for_doi(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    return include_readme(graph, repo_entity, repo, include_check_for_doi=True)


def include_readme_with_sections_and_check_for_doi(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    return include_readme(graph, repo_entity, repo, include_sections=True, include_check_for_doi=True)


def run_validation(data_graph, shapes_graph):
    result = validate(data_graph,
                      shacl_graph=shapes_graph,
                      ont_graph=None,
                      inference='rdfs',
                      abort_on_first=False,
                      allow_infos=False,
                      allow_warnings=False,
                      meta_shacl=False,
                      advanced=False,
                      js=False,
                      debug=False)

    return result


def test_repo_against_specs(github_access_token: str = "", repo_name: str = "",
                            expected_type: str = "") -> tuple[bool, str]:
    logging.info(f"Validating repo {repo_name} using the SHACL approach..")

    shapes_graph = create_project_type_representation()
    requirements_list = get_requirements_list_for_repository_representation(shapes_graph, expected_type)
    data_graph = create_repository_representation(requirements_list, github_access_token, repo_name, expected_type)
    return_code, _, result_text = run_validation(data_graph, shapes_graph)

    return return_code, result_text


if __name__ == "__main__":
    fire.Fire(test_repo_against_specs)
