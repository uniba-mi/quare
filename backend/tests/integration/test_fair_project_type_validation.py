# TODO introduce mocking!

import pytest
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from backend.shacl_validator import create_project_type_representation, run_validation, get_number_of_violations, \
    versions_have_valid_increment

sh = Namespace("http://www.w3.org/ns/shacl#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
# Software Description Ontology (SD)
sd = Namespace("https://w3id.org/okn/o/sd#")
types = Namespace("https://example.org/repo/project-types/")
nodeShapes = Namespace("https://example.org/repo/node-shapes/")
propertyShapes = Namespace("https://example.org/repo/property-shapes/")
props = Namespace("https://example.org/repo/props/")

repo_entity = URIRef("https://testing.example.org/test-repo")
default_branch_entity = URIRef("https://testing.example.org/test-repo/tree/main")


def validate(data_graph: Graph, shapes_graph: Graph) -> int:
    return_code, _, result_text = run_validation(data_graph, shapes_graph)
    number_of_violations = get_number_of_violations(return_code, result_text)
    return number_of_violations


def add_releases_to_graph(graph: Graph, release_list: list[dict]) -> Graph:
    for release in release_list:
        release_entity = URIRef(release["html_url"])
        graph.add((release_entity, sd["hasVersionId"], Literal(release["tag_name"])))
        graph.add((repo_entity, sd["hasVersion"], release_entity))
    if versions_have_valid_increment(release_list):
        graph.add((repo_entity, props["versionsHaveValidIncrement"], Literal(True)))
    else:
        graph.add((repo_entity, props["versionsHaveValidIncrement"], Literal(False)))
    return graph


@pytest.fixture
def shapes_graph() -> Graph:
    graph = create_project_type_representation()
    graph.parse("./tests/integration/references/test_project_shapes.ttl")
    return graph


# ##########
# Tests for "nodeShapes:DescriptionOrReadme"
@pytest.fixture
def repo_with_description() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestDescriptionOrReadme"]))
    graph.add((repo_entity, sd["description"], Literal("This is a description placeholder.")))
    return graph


def test_description_or_readme_positive(shapes_graph: Graph, repo_with_description: Graph) -> None:
    number_of_violations = validate(repo_with_description, shapes_graph)
    assert number_of_violations == 0


def test_description_or_readme_negative(shapes_graph: Graph) -> None:
    empty_repo = Graph().add((repo_entity, RDF.type, types["TestDescriptionOrReadme"]))
    number_of_violations = validate(empty_repo, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "nodeShapes:PersistentId"
@pytest.fixture
def repo_with_two_releases_and_non_doi_homepage() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestPersistentId"]))
    graph.add((repo_entity, sd["website"], Literal("https://example.org")))

    release_list = [
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/0.0.1",
            "tag_name": "0.0.1"
        },
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/0.0.2",
            "tag_name": "0.0.2"
        }
    ]

    return add_releases_to_graph(graph, release_list)


def test_persistent_id_positive(shapes_graph: Graph, repo_with_two_releases_and_non_doi_homepage: Graph) -> None:
    number_of_violations = validate(repo_with_two_releases_and_non_doi_homepage, shapes_graph)
    assert number_of_violations == 0


@pytest.fixture
def repo_with_non_doi_homepage() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestPersistentId"]))
    graph.add((repo_entity, sd["website"], Literal("https://example.org")))
    return graph


def test_persistent_id_negative(shapes_graph: Graph, repo_with_non_doi_homepage: Graph) -> None:
    number_of_violations = validate(repo_with_non_doi_homepage, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:PublicRepository"
@pytest.fixture
def public_repo() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestPublicRepository"]))
    graph.add((repo_entity, props["isPrivate"], Literal(False)))
    return graph


def test_public_repository_positive(shapes_graph: Graph, public_repo: Graph) -> None:
    number_of_violations = validate(public_repo, shapes_graph)
    assert number_of_violations == 0


@pytest.fixture
def private_repo() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestPublicRepository"]))
    graph.add((repo_entity, props["isPrivate"], Literal(True)))
    return graph


def test_public_repository_negative(shapes_graph: Graph, private_repo: Graph) -> None:
    number_of_violations = validate(private_repo, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "nodeShapes:SemanticVersioning"
@pytest.fixture
def repo_with_four_valid_releases() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestSemanticVersioning"]))

    release_list = [
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/v1.8.1",
            "tag_name": "v1.8.0"
        },
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/v1.7.1",
            "tag_name": "v1.7.1"
        },
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/v1.7.3",
            "tag_name": "v1.7.2"
        },
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/2.0.0-rc.1+build.1",
            "tag_name": "2.0.0-rc.1+build.1"
        }
    ]

    return add_releases_to_graph(graph, release_list)


def test_semantic_versioning_positive(shapes_graph: Graph, repo_with_four_valid_releases: Graph) -> None:
    number_of_violations = validate(repo_with_four_valid_releases, shapes_graph)
    assert number_of_violations == 0


@pytest.fixture
def repo_with_four_releases_one_invalid() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestSemanticVersioning"]))

    release_list = [
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/v1.8.1",
            "tag_name": "v1.8.0"
        },
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/v1.7.1",
            "tag_name": "v1.7.1"
        },
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/v0.1.7.3",
            "tag_name": "v0.1.7.3"
        },
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/2.0.0-rc.1+build.1",
            "tag_name": "2.0.0-rc.1+build.1"
        }
    ]

    return add_releases_to_graph(graph, release_list)


def test_semantic_versioning_negative(shapes_graph: Graph, repo_with_four_releases_one_invalid: Graph) -> None:
    number_of_violations = validate(repo_with_four_releases_one_invalid, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:UsageNotesInReadme"
@pytest.fixture
def repo_with_readme_sections_about_usage_license() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestUsageNotesInReadme"]))
    graph.add((repo_entity, sd["hasUsageNotes"], Literal("This is a placeholder for the usage notes section.")))
    return graph


def test_usage_notes_in_readme_positive(shapes_graph: Graph,
                                        repo_with_readme_sections_about_usage_license: Graph) -> None:
    number_of_violations = validate(repo_with_readme_sections_about_usage_license, shapes_graph)
    assert number_of_violations == 0


def test_usage_notes_in_readme_negative(shapes_graph: Graph) -> None:
    empty_repo = Graph().add((repo_entity, RDF.type, types["TestUsageNotesInReadme"]))
    number_of_violations = validate(empty_repo, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:ExactlyOneLicense"
@pytest.fixture
def repo_with_one_license() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestExactlyOneLicense"]))
    license_entity = URIRef("https://testing.example.org/test-repo/blob/main/LICENSE")
    graph.add((license_entity, sd["name"], Literal("MIT License")))
    graph.add((repo_entity, sd["license"], license_entity))
    return graph


def test_exactly_one_license_positive(shapes_graph: Graph, repo_with_one_license: Graph) -> None:
    number_of_violations = validate(repo_with_one_license, shapes_graph)
    assert number_of_violations == 0


def test_exactly_one_license_negative(shapes_graph: Graph) -> None:
    empty_repo = Graph().add((repo_entity, RDF.type, types["TestExactlyOneLicense"]))
    number_of_violations = validate(empty_repo, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "nodeShapes:ExplicitCitation"
@pytest.fixture
def two_branches_repo_with_license_file() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestExplicitCitation"]))

    branch_entity = URIRef("https://testing.example.org/test-repo/tree/dev")
    graph.add((branch_entity, sd["name"], Literal("dev")))
    graph.add((repo_entity, props["hasBranch"], branch_entity))
    graph.add((branch_entity, props["isDefaultBranch"], Literal(False)))

    graph.add((default_branch_entity, sd["name"], Literal("main")))
    graph.add((repo_entity, props["hasBranch"], default_branch_entity))
    graph.add((default_branch_entity, props["isDefaultBranch"], Literal(True)))
    graph.add((default_branch_entity, props["hasFileInRootDirectory"], Literal("LICENSE")))
    return graph


@pytest.fixture
def two_branches_repo_with_citation_and_license_file(two_branches_repo_with_license_file: Graph) -> Graph:
    graph = two_branches_repo_with_license_file
    graph.add((default_branch_entity, props["hasFileInRootDirectory"], Literal("CITATION.cff")))
    return graph


def test_explicit_citation_positive(shapes_graph: Graph,
                                    two_branches_repo_with_citation_and_license_file: Graph) -> None:
    number_of_violations = validate(two_branches_repo_with_citation_and_license_file, shapes_graph)
    assert number_of_violations == 0


def test_explicit_citation_negative(shapes_graph: Graph, two_branches_repo_with_license_file: Graph) -> None:
    number_of_violations = validate(two_branches_repo_with_license_file, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:AtLeastOneTopic"
@pytest.fixture
def repo_with_three_topics() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestAtLeastOneTopic"]))
    graph.add((repo_entity, sd["keywords"], Literal("Topic 1")))
    graph.add((repo_entity, sd["keywords"], Literal("Topic 2")))
    graph.add((repo_entity, sd["keywords"], Literal("Topic 3")))
    return graph


def test_at_least_one_topic_positive(shapes_graph: Graph,
                                     repo_with_three_topics: Graph) -> None:
    number_of_violations = validate(repo_with_three_topics, shapes_graph)
    assert number_of_violations == 0


def test_at_least_one_topic_negative(shapes_graph: Graph,
                                     repo_with_three_topics: Graph) -> None:
    empty_repo = Graph().add((repo_entity, RDF.type, types["TestAtLeastOneTopic"]))
    number_of_violations = validate(empty_repo, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:InstallationInstructionsInReadme"
@pytest.fixture
def repo_with_readme_sections_introduction_citation() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestInstallationInstructionsInReadme"]))
    graph.add((repo_entity, sd["citation"], Literal("This is a placeholder for the citation section.")))
    return graph


@pytest.fixture
def repo_with_readme_sections_introduction_installation_citation(
        repo_with_readme_sections_introduction_citation: Graph) -> Graph:
    graph = repo_with_readme_sections_introduction_citation
    graph.add((repo_entity, sd["hasInstallationInstructions"],
               Literal("This is a placeholder for the installation instructions section.")))
    return graph


def test_installation_instructions_in_readme_positive(shapes_graph: Graph,
                                                      repo_with_readme_sections_introduction_installation_citation:
                                                      Graph) -> None:
    number_of_violations = validate(repo_with_readme_sections_introduction_installation_citation, shapes_graph)
    assert number_of_violations == 0


def test_installation_instructions_in_readme_negative(shapes_graph: Graph,
                                                      repo_with_readme_sections_introduction_citation: Graph) -> None:
    number_of_violations = validate(repo_with_readme_sections_introduction_citation, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "nodeShapes:SoftwareRequirements"
@pytest.fixture
def typescript_repo() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types["TestSoftwareRequirements"]))
    graph.add((repo_entity, sd["programmingLanguage"], Literal("TypeScript")))
    graph.add((default_branch_entity, sd["name"], Literal("main")))
    graph.add((repo_entity, props["hasBranch"], default_branch_entity))
    graph.add((default_branch_entity, props["isDefaultBranch"], Literal(True)))
    return graph


@pytest.fixture
def typescript_repo_with_package_json_file(typescript_repo: Graph) -> Graph:
    return typescript_repo.add(
        (default_branch_entity, props["hasFileInRootDirectory"], Literal("package.json")))


def test_software_requirements_positive(shapes_graph: Graph, typescript_repo_with_package_json_file: Graph) -> None:
    number_of_violations = validate(typescript_repo_with_package_json_file, shapes_graph)
    assert number_of_violations == 0


@pytest.fixture
def typescript_repo_with_requirements_txt_file(typescript_repo: Graph) -> Graph:
    return typescript_repo.add(
        (default_branch_entity, props["hasFileInRootDirectory"], Literal("requirements.txt")))


def test_software_requirements_negative(shapes_graph: Graph, typescript_repo_with_requirements_txt_file: Graph) -> None:
    number_of_violations = validate(typescript_repo_with_requirements_txt_file, shapes_graph)
    assert number_of_violations == 1
