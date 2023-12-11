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
def repository_with_description() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types['TestDescriptionOrReadme']))
    graph.add((repo_entity, sd["description"], Literal("This is a description placeholder.")))
    return graph


def test_description_or_readme_positive(shapes_graph: Graph, repository_with_description: Graph) -> None:
    number_of_violations = validate(repository_with_description, shapes_graph)
    assert number_of_violations == 0


def test_description_or_readme_negative(shapes_graph: Graph) -> None:
    empty_repository = Graph().add((repo_entity, RDF.type, types['TestDescriptionOrReadme']))
    number_of_violations = validate(empty_repository, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "nodeShapes:PersistentId"
@pytest.fixture
def repository_with_two_releases_and_non_doi_homepage() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types['TestPersistentId']))
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


def test_persistent_id_positive(shapes_graph: Graph, repository_with_two_releases_and_non_doi_homepage: Graph) -> None:
    number_of_violations = validate(repository_with_two_releases_and_non_doi_homepage, shapes_graph)
    assert number_of_violations == 0


@pytest.fixture
def repository_with_non_doi_homepage() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types['TestPersistentId']))
    graph.add((repo_entity, sd["website"], Literal("https://example.org")))
    return graph


def test_persistent_id_negative(shapes_graph: Graph, repository_with_non_doi_homepage: Graph) -> None:
    number_of_violations = validate(repository_with_non_doi_homepage, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:PublicRepository"
@pytest.fixture
def public_repository() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types['TestPublicRepository']))
    graph.add((repo_entity, props["isPrivate"], Literal(False)))
    return graph


def test_public_repository_positive(shapes_graph: Graph, public_repository: Graph) -> None:
    number_of_violations = validate(public_repository, shapes_graph)
    assert number_of_violations == 0


@pytest.fixture
def private_repository() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types['TestPublicRepository']))
    graph.add((repo_entity, props["isPrivate"], Literal(True)))
    return graph


def test_public_repository_negative(shapes_graph: Graph, private_repository: Graph) -> None:
    number_of_violations = validate(private_repository, shapes_graph)
    assert number_of_violations == 1


# ##########
# Test cases for "nodeShapes:SemanticVersioning"
@pytest.fixture
def repository_with_four_valid_releases() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types['TestSemanticVersioning']))

    release_list = [
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/v1.8.1",
            "tag_name": "v1.8.1"
        },
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/v1.7.1",
            "tag_name": "v1.7.1"
        },
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/v1.7.3",
            "tag_name": "v1.7.3"
        },
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/2.0.0-rc.1+build.1",
            "tag_name": "2.0.0-rc.1+build.1"
        }
    ]

    return add_releases_to_graph(graph, release_list)


def test_semantic_versioning_positive(shapes_graph: Graph, repository_with_four_valid_releases: Graph) -> None:
    number_of_violations = validate(repository_with_four_valid_releases, shapes_graph)
    assert number_of_violations == 0


@pytest.fixture
def repository_with_four_releases_one_invalid() -> Graph:
    graph = Graph()
    graph.add((repo_entity, RDF.type, types['TestSemanticVersioning']))

    release_list = [
        {
            "html_url": "https://testing.example.org/test-repo/releases/tag/v1.8.1",
            "tag_name": "v1.8.1"
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


def test_semantic_versioning_negative(shapes_graph: Graph, repository_with_four_releases_one_invalid: Graph) -> None:
    number_of_violations = validate(repository_with_four_releases_one_invalid, shapes_graph)
    assert number_of_violations == 1
