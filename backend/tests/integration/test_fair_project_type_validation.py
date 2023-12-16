import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock

from backend.shacl_validator import create_project_type_representation, validate_repo_against_specs

readme_url = "https://testing.example.org/test-repo/blob/main/README.md"


@pytest.fixture
def basic_github_repo(mocker: MockerFixture) -> MagicMock:
    modified_shapes_graph = create_project_type_representation().parse(
        "./tests/integration/references/test_project_shapes.ttl")
    mocker.patch("backend.shacl_validator.create_project_type_representation", return_value=modified_shapes_graph)
    github_repo_mock = mocker.patch("github.MainClass.Github.get_repo")
    github_repo_mock.return_value.html_url = "https://testing.example.org/test-repo"
    return github_repo_mock


# ##########
# Tests for "nodeShapes:DescriptionOrReadme"
@pytest.fixture
def repo_with_description_without_readme(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.description = "This is a description placeholder."
    basic_github_repo.return_value.get_readme.return_value = None


def test_description_or_readme_positive(repo_with_description_without_readme: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestDescriptionOrReadme")
    assert number_of_violations == 0


@pytest.fixture
def repo_without_description_or_readme(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.description = None
    basic_github_repo.return_value.get_readme.return_value = None


def test_description_or_readme_negative(repo_without_description_or_readme: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestDescriptionOrReadme")
    assert number_of_violations == 1


# ##########
# Test cases for "nodeShapes:PersistentId"
@pytest.fixture
def repo_with_two_releases_and_non_doi_homepage(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_readme.return_value = None
    basic_github_repo.return_value.homepage = "https://example.org"

    release_1 = MagicMock()
    release_1.html_url = "https://testing.example.org/test-repo/releases/tag/0.0.1"
    release_1.tag_name = "0.0.1"

    release_2 = MagicMock()
    release_2.html_url = "https://testing.example.org/test-repo/releases/tag/0.0.2"
    release_2.tag_name = "0.0.2"

    basic_github_repo.return_value.get_releases.return_value = [release_1, release_2]


def test_persistent_id_positive(repo_with_two_releases_and_non_doi_homepage: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestPersistentId")
    assert number_of_violations == 0


@pytest.fixture
def repo_with_non_doi_homepage(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_readme.return_value = None
    basic_github_repo.return_value.homepage = "https://example.org"
    basic_github_repo.return_value.get_releases.return_value = None


def test_persistent_id_negative(repo_with_non_doi_homepage: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestPersistentId")
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:PublicRepository"
@pytest.fixture
def public_repo(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.private = False


def test_public_repository_positive(public_repo: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestPublicRepository")
    assert number_of_violations == 0


@pytest.fixture
def private_repo(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.private = True


def test_public_repository_negative(private_repo: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestPublicRepository")
    assert number_of_violations == 1


# ##########
# Test cases for "nodeShapes:SemanticVersioning"
@pytest.fixture
def repo_with_four_valid_releases(basic_github_repo: MagicMock) -> None:
    release_1 = MagicMock()
    release_1.html_url = "https://testing.example.org/test-repo/releases/tag/v1.8.0"
    release_1.tag_name = "v1.8.0"

    release_2 = MagicMock()
    release_2.html_url = "https://testing.example.org/test-repo/releases/tag/v1.7.1"
    release_2.tag_name = "v1.7.1"

    release_3 = MagicMock()
    release_3.html_url = "https://testing.example.org/test-repo/releases/tag/v1.7.2"
    release_3.tag_name = "v1.7.2"

    release_4 = MagicMock()
    release_4.html_url = "https://testing.example.org/test-repo/releases/tag/2.0.0-rc.1+build.1"
    release_4.tag_name = "2.0.0-rc.1+build.1"

    basic_github_repo.return_value.get_releases.return_value.__iter__.return_value = [release_1, release_2, release_3,
                                                                                      release_4]
    basic_github_repo.return_value.get_releases.return_value.totalCount = 4


def test_semantic_versioning_positive(repo_with_four_valid_releases: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestSemanticVersioning")
    assert number_of_violations == 0


@pytest.fixture
def repo_with_four_releases_one_invalid(basic_github_repo: MagicMock) -> None:
    release_1 = MagicMock()
    release_1.html_url = "https://testing.example.org/test-repo/releases/tag/v1.8.0"
    release_1.tag_name = "v1.8.0"

    release_2 = MagicMock()
    release_2.html_url = "https://testing.example.org/test-repo/releases/tag/v1.7.1"
    release_2.tag_name = "v1.7.1"

    release_3 = MagicMock()
    release_3.html_url = "https://testing.example.org/test-repo/releases/tag/v1.7.3"
    release_3.tag_name = "v1.7.3"

    release_4 = MagicMock()
    release_4.html_url = "https://testing.example.org/test-repo/releases/tag/2.0.0-rc.1+build.1"
    release_4.tag_name = "2.0.0-rc.1+build.1"

    basic_github_repo.return_value.get_releases.return_value.__iter__.return_value = [release_1, release_2, release_3,
                                                                                      release_4]
    basic_github_repo.return_value.get_releases.return_value.totalCount = 4


def test_semantic_versioning_negative(repo_with_four_releases_one_invalid: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestSemanticVersioning")
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:UsageNotesInReadme"
@pytest.fixture
def repo_with_readme_sections_about_usage_license(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_readme.return_value.html_url = readme_url
    basic_github_repo.return_value.get_readme.return_value.decoded_content = \
        (b'# About\nPlaceholder about section.\n\n# Usage\nPlaceholder usage section.\n\n'
         b'# License\nPlaceholder license section.\n')


def test_usage_notes_in_readme_positive(repo_with_readme_sections_about_usage_license: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestUsageNotesInReadme")
    assert number_of_violations == 0


@pytest.fixture
def repo_without_readme(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_readme.return_value = None


def test_usage_notes_in_readme_negative(repo_without_readme: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestUsageNotesInReadme")
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:ExactlyOneLicense"
@pytest.fixture
def repo_with_one_license(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_license.return_value.html_url = \
        "https://testing.example.org/test-repo/blob/main/LICENSE"
    basic_github_repo.return_value.get_license.return_value.license.name = "MIT License"


def test_exactly_one_license_positive(repo_with_one_license: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestExactlyOneLicense")
    assert number_of_violations == 0


@pytest.fixture
def repo_without_license(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_license.return_value = None


def test_exactly_one_license_negative(repo_without_license: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestExactlyOneLicense")
    assert number_of_violations == 1


# ##########
# Test cases for "nodeShapes:ExplicitCitation"
@pytest.fixture
def two_branches_repo_without_readme(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_readme.return_value = None

    basic_github_repo.return_value.default_branch = "main"
    branch_1 = MagicMock()
    branch_1.name = "main"

    branch_2 = MagicMock()
    branch_2.name = "dev"

    basic_github_repo.return_value.get_branches.return_value = [branch_1, branch_2]


@pytest.fixture
def two_branches_repo_with_citation_and_license_file(basic_github_repo: MagicMock,
                                                     two_branches_repo_without_readme: MagicMock) -> None:
    file_1 = MagicMock()
    file_1.type = "blob"
    file_1.path = "LICENSE"

    file_2 = MagicMock()
    file_2.type = "blob"
    file_2.path = "CITATION.cff"

    basic_github_repo.return_value.get_git_tree.return_value.tree = [file_1, file_2]


def test_explicit_citation_positive(two_branches_repo_with_citation_and_license_file: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestExplicitCitation")
    assert number_of_violations == 0


@pytest.fixture
def two_branches_repo_with_license_file(basic_github_repo: MagicMock,
                                        two_branches_repo_without_readme: MagicMock) -> None:
    file_1 = MagicMock()
    file_1.type = "blob"
    file_1.path = "LICENSE"

    basic_github_repo.return_value.get_git_tree.return_value.tree = [file_1]


def test_explicit_citation_negative(two_branches_repo_with_license_file: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestExplicitCitation")
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:AtLeastOneTopic"
@pytest.fixture
def repo_with_three_topics(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_topics.return_value = ["Topic 1", "Topic 2", "Topic 3"]


def test_at_least_one_topic_positive(repo_with_three_topics: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestAtLeastOneTopic")
    assert number_of_violations == 0


@pytest.fixture
def repo_without_topics(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_topics.return_value = None


def test_at_least_one_topic_negative(repo_without_topics: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestAtLeastOneTopic")
    assert number_of_violations == 1


# ##########
# Test cases for "propertyShapes:InstallationInstructionsInReadme"
@pytest.fixture
def repo_with_readme_sections_introduction_installation_citation(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_readme.return_value.html_url = readme_url
    basic_github_repo.return_value.get_readme.return_value.decoded_content = \
        (b'# Introduction\nPlaceholder introduction section.\n\n# Installation\nPlaceholder installation section.\n\n'
         b'# Citation\nPlaceholder citation section.\n')


def test_installation_instructions_in_readme_positive(
        repo_with_readme_sections_introduction_installation_citation: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestInstallationInstructionsInReadme")
    assert number_of_violations == 0


@pytest.fixture
def repo_with_readme_sections_introduction_citation(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_readme.return_value.html_url = readme_url
    basic_github_repo.return_value.get_readme.return_value.decoded_content = \
        b'# Introduction\nPlaceholder introduction section.\n\n# Citation\nPlaceholder citation section.\n'


def test_installation_instructions_in_readme_negative(
        repo_with_readme_sections_introduction_citation: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestInstallationInstructionsInReadme")
    assert number_of_violations == 1


# ##########
# Test cases for "nodeShapes:SoftwareRequirements"
@pytest.fixture
def one_branch_typescript_repo(basic_github_repo: MagicMock) -> None:
    basic_github_repo.return_value.get_readme.return_value = None
    basic_github_repo.return_value.language = "TypeScript"

    basic_github_repo.return_value.default_branch = "main"
    branch = MagicMock()
    branch.name = "main"
    basic_github_repo.return_value.get_branches.return_value = [branch]

    file = MagicMock()
    file.type = "blob"
    file.path = "package.json"
    basic_github_repo.return_value.get_git_tree.return_value.tree = [file]


@pytest.fixture
def typescript_repo_with_package_json_file(basic_github_repo: MagicMock, one_branch_typescript_repo: MagicMock) -> None:
    file = MagicMock()
    file.type = "blob"
    file.path = "package.json"
    basic_github_repo.return_value.get_git_tree.return_value.tree = [file]


def test_software_requirements_positive(typescript_repo_with_package_json_file: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestSoftwareRequirements")
    assert number_of_violations == 0


@pytest.fixture
def typescript_repo_with_requirements_txt_file(basic_github_repo: MagicMock,
                                               one_branch_typescript_repo: MagicMock) -> None:
    file = MagicMock()
    file.type = "blob"
    file.path = "requirements.txt"
    basic_github_repo.return_value.get_git_tree.return_value.tree = [file]


def test_software_requirements_negative(typescript_repo_with_requirements_txt_file: MagicMock) -> None:
    _, number_of_violations, _ = validate_repo_against_specs(repo_name="test-repo",
                                                             expected_type="TestSoftwareRequirements")
    assert number_of_violations == 1
