#!/usr/bin/env python3

import logging
import re
from itertools import pairwise

import fire
import markdown
from bs4 import BeautifulSoup
from github import Github, UnknownObjectException
from packaging import version
from packaging.version import Version
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

types = Namespace("https://example.org/repo/project-types/")
props = Namespace("https://example.org/repo/props/")


def get_project_type_specifications():
    with open("data/shacl/project-shapes.ttl") as raw_shapes_graph:

        raw_shapes_graph = list(raw_shapes_graph)

        type_spec_indices = []

        for index, line in enumerate(raw_shapes_graph):
            if line.startswith("types:"):
                current_type = line.replace("\n", "").strip()
                first_index = index + 2

            if (("sh:property" in line) or ("sh:node" in line)) & (" ." in line):
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

        split_by_comments = re.split("# ", spec_block)

        # If there are comments on this project type, split based on these.
        if len(split_by_comments) > 1:
            specs = [spec.replace("sh:node ", "→ ") for spec in split_by_comments]
            specs = [spec.replace("sh:property ", "→ ") for spec in specs]
        else:
            specs = re.split(r"sh:property\s+|sh:node\s+", spec_block)

        specs = [spec.strip().removesuffix(";") for spec in specs]
        specs = [spec.strip().removesuffix(".") for spec in specs]

        project_type_specifications[project_type.removeprefix("types:")] = specs[1:]  # At index 0 of specs is "".

    return project_type_specifications


def create_project_type_representation():
    # Here, "graph merging" is used (https://rdflib.readthedocs.io/en/stable/merging.html).
    graph = Graph()
    graph.parse("./data/shacl/property-shapes.ttl")
    graph.parse("./data/shacl/node-shapes.ttl")
    graph.parse("./data/shacl/project-shapes.ttl")

    return graph


def create_repository_representation(access_token="", repo_name="", expected_type=""):
    graph = Graph()
    github = Github(access_token) if access_token else Github()

    # get repo
    repo = github.get_repo(repo_name)
    repo_entity = URIRef(repo.html_url)
    graph.add((repo_entity, RDF.type, types[expected_type]))

    return add_required_properties_to_graph(graph, repo_entity, repo)


# TODO always the same parameters
def add_required_properties_to_graph(graph, repo_entity, repo):
    # TODO make method calls dependent on project type
    graph = include_visibility(graph, repo_entity, repo)
    graph = include_topics(graph, repo_entity, repo)
    graph = include_description(graph, repo_entity, repo)
    graph = include_homepage(graph, repo_entity, repo)
    graph = include_main_language(graph, repo_entity, repo)
    graph = include_releases(graph, repo_entity, repo, check_version_increment=True)  # TODO type dependent
    graph = include_branches(graph, repo_entity, repo)
    graph = include_default_branch(graph, repo_entity, repo, include_root_directory_files=True)  # TODO type dependent
    graph = include_issues(graph, repo_entity, repo)
    graph = include_license(graph, repo_entity, repo)
    graph = include_readme(graph, repo_entity, repo, include_sections=True,
                           include_check_for_doi=True)  # TODO type dependent
    return graph


def include_visibility(graph, repo_entity, repo):
    return graph.add((repo_entity, props["is_private"], Literal(repo.private)))


def include_topics(graph, repo_entity, repo):
    topic_list = repo.get_topics()
    if topic_list:
        for topic in topic_list:
            graph.add((repo_entity, props["has_topic"], Literal(topic)))
    return graph


def include_description(graph, repo_entity, repo):
    if repo.description:
        graph.add((repo_entity, props["has_description"], Literal(repo.description)))
    return graph


def include_homepage(graph, repo_entity, repo):
    if repo.homepage:
        graph.add((repo_entity, props["has_homepage"], Literal(repo.homepage)))
    return graph


def include_main_language(graph, repo_entity, repo):
    if repo.language:
        graph.add((repo_entity, props["has_main_language"], Literal(repo.language)))
    return graph


def include_releases(graph, repo_entity, repo, check_version_increment=False):
    release_list = repo.get_releases()
    if not release_list:
        return graph

    for release in release_list:
        release_entity = URIRef(release.html_url)
        graph.add((release_entity, props["has_tag_name"], Literal(release.tag_name)))
        graph.add((repo_entity, props["has_release"], release_entity))

    if not check_version_increment:
        return graph

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
    return graph


def pair_has_valid_version_increment(pair: tuple[Version, Version]):
    # If the first number (major) is increased, the second (minor) and third (micro) must be set to zero.
    if (pair[0].major + 1 == pair[1].major) & (pair[1].minor == 0) & (pair[1].micro == 0):
        return True

    # If minor in increased, micro must be set to zero.
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


def include_branches(graph, repo_entity, repo):
    branch_list = repo.get_branches()
    if branch_list:
        for branch in branch_list:
            branch_entity = URIRef(f"{repo.html_url}/tree/{branch.name}")
            graph.add((branch_entity, props["has_name"], Literal(branch.name)))
            graph.add((repo_entity, props["has_branch"], branch_entity))
    return graph


def include_default_branch(graph, repo_entity, repo, include_root_directory_files=False):
    default_branch_name = repo.default_branch
    if not default_branch_name:
        return graph

    branch_entity = URIRef(f"{repo.html_url}/tree/{default_branch_name}")
    graph.add((branch_entity, props["has_name"], Literal(default_branch_name)))
    graph.add((repo_entity, props["has_default_branch"], branch_entity))

    if not include_root_directory_files:
        return graph

    git_tree = repo.get_git_tree(default_branch_name)
    for item in git_tree.tree:
        if item.type == "blob":
            graph.add((branch_entity, props["has_file_in_root_directory"], Literal(item.path)))
    return graph


def include_issues(graph, repo_entity, repo):
    issue_list = repo.get_issues()
    if issue_list:
        for issue in issue_list:
            issue_entity = URIRef(issue.html_url)
            graph.add((issue_entity, props["has_state"], Literal(issue.state)))
            graph.add((repo_entity, props["has_issue"], issue_entity))
    return graph


def include_license(graph, repo_entity, repo):
    try:
        license_data = repo.get_license()
        if license_data:
            graph.add((repo_entity, props["has_license"], Literal(license_data.license.name)))
    except UnknownObjectException as e:
        logging.exception(f"No license could be retrieved due to: {e}")

    return graph


def include_readme(graph, repo_entity, repo, include_sections=False, include_check_for_doi=False):
    try:
        readme = repo.get_readme()
    except UnknownObjectException as e:
        logging.exception(f"No README file could be retrieved due to: {e}")
        return graph

    if not readme:
        return graph

    readme_entity = URIRef(readme.html_url)
    graph.add((repo_entity, props["has_readme"], readme_entity))

    if not (include_sections or include_check_for_doi):
        return graph

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

    return graph


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


def test_repo_against_specs(github_access_token="", repo_name="", expected_type=""):
    logging.info(f"Validating repo {repo_name} using the SHACL approach..")

    shapes_graph = create_project_type_representation()
    data_graph = create_repository_representation(
        github_access_token, repo_name, expected_type)
    return_code, _, result_text = run_validation(data_graph, shapes_graph)

    return return_code, result_text


if __name__ == "__main__":
    fire.Fire(test_repo_against_specs)
