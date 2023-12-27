import shacl_verbalizer


def run_verbalizer(report, repo_name, repo_type) -> str:
    return shacl_verbalizer.verbalize(report, repo_name, repo_type)
