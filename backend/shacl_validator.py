#!/usr/bin/env python3

import logging
import re
from itertools import pairwise

import fire
import markdown
from bs4 import BeautifulSoup, Tag
from github import Github, UnknownObjectException, GithubException
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from packaging import version
from packaging.version import Version
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

types = Namespace("https://example.org/repo/project-types/")
# Software Description Ontology (SD)
sd = Namespace("https://w3id.org/okn/o/sd#")
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
        "BranchesIncludingRootDirFilesOfDefaultBranch": include_branches_with_root_dir_files_of_default_branch,
        "Description": include_description,
        "Homepage": include_homepage,
        "Issues": include_issues,
        "License": include_license,
        "MainLanguage": include_main_language,
        "Readme": include_readme,
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
    graph.add((repo_entity, props["isPrivate"], Literal(repo.private)))


def include_topics(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    topic_list = repo.get_topics()
    if topic_list:
        for topic in topic_list:
            graph.add((repo_entity, sd["keywords"], Literal(topic)))


def include_description(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    if repo.description:
        graph.add((repo_entity, sd["description"], Literal(repo.description)))


def include_homepage(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    if repo.homepage:
        graph.add((repo_entity, sd["website"], Literal(repo.homepage)))


def include_main_language(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    if repo.language:
        graph.add((repo_entity, sd["programmingLanguage"], Literal(repo.language)))


def include_releases(graph: Graph, repo_entity: URIRef, repo: Repository,
                     check_version_increment: bool = False) -> None:
    release_list = repo.get_releases()
    if not release_list:
        return

    for release in release_list:
        release_entity = URIRef(release.html_url)
        graph.add((release_entity, sd["hasVersionId"], Literal(release.tag_name)))
        graph.add((repo_entity, sd["hasVersion"], release_entity))

    if not (check_version_increment and release_list.totalCount > 0):
        return

    if versions_have_valid_increment(release_list):
        graph.add((repo_entity, props["versionsHaveValidIncrement"], Literal(True)))
    else:
        graph.add((repo_entity, props["versionsHaveValidIncrement"], Literal(False)))


def include_releases_with_increment_check(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    return include_releases(graph, repo_entity, repo, check_version_increment=True)


def versions_have_valid_increment(release_list: PaginatedList | list[dict]) -> bool:
    try:
        version_list = [version.parse(release.tag_name.removeprefix("v")) for release in release_list]
        sorted_version_list = sorted(version_list)
    except ValueError:
        return False

    return_value = True
    for pair in pairwise(sorted_version_list):
        if not version_pair_has_valid_version_increment(pair):
            return_value = False
            break

    return return_value


def version_pair_has_valid_version_increment(pair: tuple[Version, Version]) -> bool:
    # If the first number (major) is increased, the second (minor) and third (micro) must be set to zero.
    if (pair[0].major + 1 == pair[1].major) & (pair[1].minor == 0) & (pair[1].micro == 0):
        return True

    # If minor is increased, micro must be set to zero.
    if (pair[0].major == pair[1].major) & (pair[0].minor + 1 == pair[1].minor) & (pair[1].micro == 0):
        return True

    # If micro is increased, major and minor must be unchanged.
    if (pair[0].major == pair[1].major) & (pair[0].minor == pair[1].minor) & (pair[0].micro + 1 == pair[1].micro):
        return True

    # If major, minor and macro are the same in both versions, the versions have to differ in the suffix.
    if (pair[0].major == pair[1].major) & (pair[0].minor == pair[1].minor) & (pair[0].micro == pair[1].micro) & (
            pair[0] != pair[1]):
        return True

    return False


def include_branches(graph: Graph, repo_entity: URIRef, repo: Repository,
                     include_root_dir_files_of_default_branch: bool = False) -> None:
    branch_list = repo.get_branches()
    default_branch_name = repo.default_branch

    for branch in branch_list:
        branch_entity = URIRef(f"{repo.html_url}/tree/{branch.name}")
        graph.add((branch_entity, sd["name"], Literal(branch.name)))
        graph.add((repo_entity, props["hasBranch"], branch_entity))

        if branch.name == default_branch_name:
            graph.add((branch_entity, props["isDefaultBranch"], Literal(True)))
        else:
            graph.add((branch_entity, props["isDefaultBranch"], Literal(False)))

    if not include_root_dir_files_of_default_branch:
        return

    try:
        git_tree = repo.get_git_tree(default_branch_name)
    except GithubException as e:
        logging.exception(f"No files of the default branch could be retrieved due to: {e}")
        return

    default_branch_entity = URIRef(f"{repo.html_url}/tree/{default_branch_name}")
    for item in git_tree.tree:
        if item.type == "blob":
            graph.add((default_branch_entity, props["hasFileInRootDirectory"], Literal(item.path)))


def include_branches_with_root_dir_files_of_default_branch(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    return include_branches(graph, repo_entity, repo, include_root_dir_files_of_default_branch=True)


def include_issues(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    issue_list = repo.get_issues()
    if issue_list:
        for issue in issue_list:
            issue_entity = URIRef(issue.html_url)
            graph.add((issue_entity, props["hasState"], Literal(issue.state)))
            graph.add((repo_entity, props["hasIssue"], issue_entity))


def include_license(graph: Graph, repo_entity: URIRef, repo: Repository) -> None:
    try:
        license_data = repo.get_license()
        if license_data:
            license_entity = URIRef(license_data.html_url)
            graph.add((license_entity, sd["name"], Literal(license_data.license.name)))
            graph.add((repo_entity, sd["license"], license_entity))
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
    graph.add((repo_entity, sd["readme"], readme_entity))

    if not (include_sections or include_check_for_doi):
        return

    md = markdown.Markdown()
    html = md.convert(readme.decoded_content.decode())
    soup = BeautifulSoup(html, "html.parser")
    if include_sections:
        process_readme_sections(graph, repo_entity, soup)

    if include_check_for_doi:
        # Check whether there is at least one DOI in the README file (as text or link href).
        # Regex adapted from https://www.crossref.org/blog/dois-and-matching-regular-expressions/
        doi_pattern = re.compile(r"https://doi\.org/10\.\d{4,}/[-._;()/:A-Z0-9]+")
        if soup.find_all(string=doi_pattern) or soup.find_all(href=doi_pattern):
            graph.add((readme_entity, props["containsDoi"], Literal("true")))
        else:
            graph.add((readme_entity, props["containsDoi"], Literal("false")))


def process_readme_sections(graph: Graph, repo_entity: URIRef, soup: BeautifulSoup) -> None:
    installation_instructions_keywords = ("installation", "how to install", "setup", "set up", "setting up")
    usage_notes_keywords = ("usage", "how to use", "manual", "user manual")
    sw_requirements_keywords = ("dependencies", "requirements")

    heading_tags = ["h" + str(ctr) for ctr in range(1, 7)]
    headings_elems = [soup.find_all(tag)
                      for tag in heading_tags if soup.find_all(tag)]
    headings_elems = [item for sublist in headings_elems for item in sublist]

    for heading in headings_elems:
        lower_cased_heading = heading.text.lower()

        if lower_cased_heading.startswith(installation_instructions_keywords):
            content = get_content_from_readme_section(heading, heading_tags)
            graph.add((repo_entity, sd["hasInstallationInstructions"], Literal(content)))
            continue

        if lower_cased_heading.startswith(usage_notes_keywords):
            content = get_content_from_readme_section(heading, heading_tags)
            graph.add((repo_entity, sd["hasUsageNotes"], Literal(content)))
            continue

        if lower_cased_heading.startswith("purpose"):
            content = get_content_from_readme_section(heading, heading_tags)
            graph.add((repo_entity, sd["hasPurpose"], Literal(content)))
            continue

        if lower_cased_heading.startswith(sw_requirements_keywords):
            content = get_content_from_readme_section(heading, heading_tags)
            graph.add((repo_entity, sd["softwareRequirements"], Literal(content)))
            continue

        if lower_cased_heading.startswith("citation"):
            content = get_content_from_readme_section(heading, heading_tags)
            graph.add((repo_entity, sd["citation"], Literal(content)))


def get_content_from_readme_section(heading_elem: Tag, heading_tags: list[str]) -> str:
    content = ""
    for sibling in heading_elem.next_siblings:
        if isinstance(sibling, Tag) and sibling.name in heading_tags:
            break
        stripped_text = sibling.text.strip()
        if stripped_text:
            content += stripped_text + " "
    return content.rstrip()


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


def validate_repo_against_specs(github_access_token: str = "", repo_name: str = "",
                                expected_type: str = "") -> tuple[bool, int, str]:
    logging.info(f"Validating repo {repo_name} using the SHACL approach..")

    shapes_graph = create_project_type_representation()
    requirements_list = get_requirements_list_for_repository_representation(shapes_graph, expected_type)
    data_graph = create_repository_representation(requirements_list, github_access_token, repo_name, expected_type)
    return_code, _, result_text = run_validation(data_graph, shapes_graph)
    number_of_violations = get_number_of_violations(return_code, result_text)

    return return_code, number_of_violations, result_text


def get_number_of_violations(return_code: bool, result_text: str) -> int:
    if return_code:
        return 0
    line_with_number_of_violations = result_text.splitlines()[2]
    number_of_violations = re.search(r"Results\s+\((\d+)\)", line_with_number_of_violations).group(1)
    return int(number_of_violations)


if __name__ == "__main__":
    fire.Fire(validate_repo_against_specs)
