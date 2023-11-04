#!/usr/bin/env python3

import logging
import re

import fire
import markdown
from bs4 import BeautifulSoup
from github import Github, UnknownObjectException
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

            if (("sh:property" in line) | ("sh:node" in line)) & (" ." in line):
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
            specs = re.split("sh:property\s+|sh:node\s+", spec_block)

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

    # process visibility
    graph.add((repo_entity, props["is_private"], Literal(repo.private)))

    # process topics
    topic_list = repo.get_topics()
    if topic_list:
        for topic in topic_list:
            graph.add((repo_entity, props["has_topic"], Literal(topic)))

    # process description
    if repo.description:
        graph.add((repo_entity, props["has_description"], Literal(repo.description)))

    # process homepage
    if repo.homepage:
        graph.add((repo_entity, props["has_homepage"], Literal(repo.homepage)))

    # process main language
    if repo.language:
        graph.add((repo_entity, props["has_main_language"], Literal(repo.language)))

    # process release and tag information
    release_list = repo.get_releases()
    if release_list:
        for release in release_list:
            release_entity = URIRef(release.html_url)
            graph.add((release_entity, props["has_tag_name"], Literal(release.tag_name)))
            graph.add((repo_entity, props["has_release"], release_entity))

    # process branch information
    branch_list = repo.get_branches()
    if branch_list:
        for branch in branch_list:
            branch_entity = URIRef(f"{repo.html_url}/tree/{branch.name}")
            graph.add((branch_entity, props["has_name"], Literal(branch.name)))
            graph.add((repo_entity, props["has_branch"], branch_entity))

    default_branch_name = repo.default_branch
    if default_branch_name:
        branch_entity = URIRef(f"{repo.html_url}/tree/{default_branch_name}")
        graph.add((repo_entity, props["has_default_branch"], branch_entity))

        # process files in the root directory of the default branch
        git_tree = repo.get_git_tree(default_branch_name)
        for item in git_tree.tree:
            if item.type == "blob":
                graph.add((branch_entity, props["has_file_in_root_directory"], Literal(item.path)))

    # process issue information
    issue_list = repo.get_issues()
    if issue_list:
        for issue in issue_list:
            issue_entity = URIRef(issue.html_url)
            graph.add((issue_entity, props["has_state"], Literal(issue.state)))
            graph.add((repo_entity, props["has_issue"], issue_entity))

    # process license information
    try:
        license = repo.get_license()
        if license:
            graph.add((repo_entity, props["has_license"], Literal(license.license.name)))
    except UnknownObjectException as e:
        logging.exception(f"No license could be retrieved due to: {e}")

    # process readme information
    try:
        readme = repo.get_readme()
        if readme:
            # identify sections
            md = markdown.Markdown()
            html = md.convert(readme.decoded_content.decode())
            soup = BeautifulSoup(html, "html.parser")

            heading_tags = ["h" + str(ctr) for ctr in range(1, 7)]
            headings_elems = [soup.find_all(tag)
                              for tag in heading_tags if soup.find_all(tag)]
            headings_elems = [
                item for sublist in headings_elems for item in sublist]
            headings = [item.text for item in headings_elems]

            # create entities
            readme_entity = URIRef(readme.html_url)
            graph.add((repo_entity, props["has_readme"], readme_entity))

            for heading in headings:
                graph.add((readme_entity, props["has_section"], Literal(heading)))

            # Check whether there is at least one DOI in the README file (as text or link href).
            # Regex adapted from https://www.crossref.org/blog/dois-and-matching-regular-expressions/
            doi_pattern = re.compile(r"https://doi\.org/10\.\d{4,}/[-._;()/:A-Z0-9]+")
            if soup.find_all(string=doi_pattern) or soup.find_all(href=doi_pattern):
                graph.add((readme_entity, props["contains_doi"], Literal("true")))
            else:
                graph.add((readme_entity, props["contains_doi"], Literal("false")))

    except UnknownObjectException as e:
        logging.exception(f"No README file could be retrieved due to: {e}")

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
