#!/usr/bin/env python3

import logging

import fire
import markdown
from bs4 import BeautifulSoup
from github import Github, UnknownObjectException
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

types = Namespace("https://example.org/repo/project-types/")
props = Namespace("https://example.org/repo/props/")
entities = Namespace("https://example.org/repo/entities/")


def get_project_type_specifications():

    project_type_specifications = {}

    with open("./data/shacl-project-shapes.ttl") as raw_shapes_graph:

        raw_shapes_graph = list(raw_shapes_graph)

        type_spec_indices = []

        for index, line in enumerate(raw_shapes_graph):
            if line.startswith("types:"):
                current_type = line.replace("\n", "").strip()
                first_index = index + 3

            if "] ." in line:
                last_index = index

                type_spec_indices.append(
                    (current_type, first_index, last_index))

        for project_type, first_index, last_index in type_spec_indices:
            spec_block = "".join(raw_shapes_graph[first_index:last_index])
            spec_block = spec_block.replace("\t", "")

            specs = spec_block.split("], [")

            project_type_specifications[project_type.replace(
                "types:", "")] = specs

    return project_type_specifications


def create_project_type_representation():
    graph = Graph()
    graph.parse("./data/shacl-project-shapes.ttl")

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
        graph.add(
            (repo_entity, props["has_description"], Literal(repo.description)))

    # process release information
    release_list = repo.get_releases()
    if release_list:
        for release in release_list:
            graph.add(
                (repo_entity, props["has_release"], URIRef(release.html_url)))

    # process branch information
    branch_list = repo.get_branches()
    if branch_list:
        for branch in branch_list:
            graph.add((repo_entity, props["has_branch"], URIRef(
                f"{repo.html_url}/tree/{branch.name}")))

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
            graph.add((repo_entity, props["has_license"],
                       Literal(license.license.name)))
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
                graph.add(
                    (readme_entity, props["has_section"], Literal(heading)))

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
