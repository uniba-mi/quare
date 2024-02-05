import shacl_verbalizer


def run_verbalizer(report) -> list[str]:
    return shacl_verbalizer.verbalize(report)
