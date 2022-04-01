#!/usr/bin/env python3

import logging

import fire
import markdown
from bs4 import BeautifulSoup
from github import Github
from owlready2 import (AllDifferent, AllDisjoint, DataProperty,
                       FunctionalProperty, Not, Thing, close_world,
                       get_ontology, sync_reasoner_pellet)

onto = get_ontology("http://example.org/onto.owl")


def create_project_type_representation():
    # create classes and properties
    with onto:
        class DefaultProject(Thing):
            pass

        # general properties
        class has_state(DataProperty, FunctionalProperty):
            domain = [Thing]
            range = [str]
            python_name = "state"

        class has_content(DataProperty, FunctionalProperty):
            domain = [Thing]
            range = [str]
            python_name = "content"

        # repository related classes and properties
        class is_private(DataProperty, FunctionalProperty):
            domain = [DefaultProject]
            range = [bool]
            python_name = "private"

        # topic related classes and properties
        class Topic(Thing):
            pass

        class has_topic(DefaultProject >> Topic):
            python_name = "topics"

        # description related classes and properties
        class Description(Thing):
            pass

        class has_description(DefaultProject >> Description):
            python_name = "description"

        # branch related classes and properties
        class Branch(Thing):
            pass

        class has_branch(DefaultProject >> Branch):
            python_name = "branches"

        class MainBranch(Branch):
            equivalent_to = [
                Branch &
                has_content.value("main")
            ]

        # issue related classes and properties
        class Issue(Thing):
            pass

        class has_issue(DefaultProject >> Issue):
            python_name = "issues"

        class OpenIssue(Issue):
            equivalent_to = [
                Issue &
                has_state.value("open")
            ]

        # release related classes and properties
        class Release(Thing):
            pass

        class has_release(DefaultProject >> Release):
            python_name = "releases"

        # license related classes and properties
        class has_license(DataProperty, FunctionalProperty):
            domain = [DefaultProject]
            range = [str]
            python_name = "license"

        # readme related classes and properties
        class Readme(Thing):
            pass

        class has_readme(DefaultProject >> Readme):
            python_name = "readme"

        class ReadmeSection(Thing):
            pass

        class has_readme_section(DefaultProject >> ReadmeSection):
            python_name = "readme_sections"

        class InstallationSection(ReadmeSection):
            equivalent_to = [
                ReadmeSection &
                has_content.value("Installation")
            ]

        class UsageSection(ReadmeSection):
            equivalent_to = [
                ReadmeSection &
                has_content.value("Usage")
            ]

        class PurposeSection(ReadmeSection):
            equivalent_to = [
                ReadmeSection &
                has_content.value("Purpose")
            ]

        AllDisjoint([InstallationSection, UsageSection, PurposeSection])

        # project type specification
        class FinishedResearchProject(DefaultProject):
            equivalent_to = [
                DefaultProject &
                is_private.value(False) &
                has_topic.min(1, Topic) &
                has_description.exactly(1, Description) &
                has_branch.exactly(1, MainBranch) &
                Not(has_issue.some(OpenIssue)) &
                has_release.min(1, Release) &
                has_license.value("GNU General Public License v3.0") &
                has_readme.exactly(1, Readme) &
                has_readme_section.exactly(1, InstallationSection) &
                has_readme_section.exactly(1, UsageSection)
            ]

        class OngoingResearchProject(DefaultProject):
            equivalent_to = [
                DefaultProject &
                is_private.value(True) &
                has_branch.min(2, Branch)
            ]

        class TeachingTool(DefaultProject):
            equivalent_to = [
                DefaultProject &
                is_private.value(False) &
                has_topic.min(1, Topic) &
                has_description.exactly(1, Description) &
                has_branch.min(2, Branch) &
                has_release.min(1, Release) &
                has_license.value("MIT License") &
                has_readme.exactly(1, Readme) &
                has_readme_section.exactly(1, UsageSection)
            ]

        class InternalDocumentation(DefaultProject):
            equivalent_to = [
                DefaultProject &
                is_private.value(True) &
                has_description.exactly(1, Description) &
                has_readme.exactly(1, Readme) &
                has_readme_section.exactly(1, InstallationSection)
            ]


def get_project_type_specifcations():

    create_project_type_representation()

    with onto:
        raw_subclasses = list(onto.DefaultProject.subclasses())
        project_type_definitions = {str(subclass).split("onto.")[1]: str(subclass._equivalent_to[0]).split(" & ")
                                    for subclass in raw_subclasses}

    return project_type_definitions


def create_repository_representation(github_access_token="", repo_name="", expected_type=""):

    with onto:
        if github_access_token:
            github = Github(github_access_token)
        else:
            github = Github()

        # get repo
        repo = github.get_repo(repo_name)

        # process visibility
        repo_entity_params = {"private": repo.private}

        # process topics
        topic_list = repo.get_topics()
        if topic_list:
            repo_entity_params["topics"] = [onto.Topic(
                content=topic) for topic in topic_list]

        # process description
        if repo.description:
            repo_entity_params["description"] = [
                onto.Description(content=repo.description)]

        # process release information
        release_entities = []

        release_list = repo.get_releases()
        if release_list:
            for release in release_list:
                release_entity = onto.Release()
                release_entity.iri = release.html_url
                release_entities.append(release_entity)

            # AllDifferent(release_entities)
            repo_entity_params["releases"] = release_entities

        # process branch information
        branch_entities = []

        branch_list = repo.get_branches()
        if branch_list:
            for branch in branch_list:
                branch_entity = onto.Branch(content=branch.name)
                branch_entity.iri = f"{repo.html_url}/tree/{branch.name}"
                branch_entities.append(branch_entity)

            AllDifferent(branch_entities)
            repo_entity_params["branches"] = branch_entities

        # process issue information
        issue_entities = []

        issue_list = repo.get_issues()
        if issue_list:
            for issue in issue_list:
                issue_entity = onto.Issue(state=issue.state)
                issue_entity.iri = issue.html_url
                issue_entities.append(issue_entity)

            repo_entity_params["issues"] = issue_entities

        # process license information
        license = repo.get_license()

        if license:
            repo_entity_params["license"] = license.license.name

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
                readme_entity = onto.Readme()
                readme_entity.iri = readme.html_url

                repo_entity_params["readme"] = [readme_entity]

                section_entities = [
                    onto.ReadmeSection(content=heading) for heading in headings]
                AllDifferent(section_entities)
                repo_entity_params["readme_sections"] = section_entities

        except Exception as e:
            print(f"No README file could be retrieved due to: {e}")

        # create and thereby test repo entity against expected type
        if expected_type == "FinishedResearchProject":
            repo_entity = onto.FinishedResearchProject(**repo_entity_params)
        elif expected_type == "OngoingResearchProject":
            repo_entity = onto.OngoingResearchProject(**repo_entity_params)
        elif expected_type == "TeachingTool":
            repo_entity = onto.TeachingTool(**repo_entity_params)
        elif expected_type == "InternalDocumentation":
            repo_entity = onto.InternalDocumentation(**repo_entity_params)

        repo_entity.iri = repo.html_url

    close_world(onto.DefaultProject)


def run_validation():

    sync_reasoner_pellet(debug=2)


def test_repo_against_specs(github_access_token="", repo_name="", expected_type=""):

    logging.info(f"Validating repo {repo_name} using the OWL approach..")

    create_project_type_representation()
    create_repository_representation(
        github_access_token, repo_name, expected_type)
    run_validation()


if __name__ == "__main__":
    fire.Fire(test_repo_against_specs)
