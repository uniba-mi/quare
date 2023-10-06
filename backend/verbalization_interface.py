import logging
import shacl_verbalizer
import owl_verbalizer

logger = logging.getLogger(__name__)


def run_verbalizer(report, repo_name, repo_type, method):

    if method == "owl":
        verbalized_explanation = owl_verbalizer.verbalize(report, repo_name, repo_type)

    elif method == "shacl":
        verbalized_explanation = shacl_verbalizer.verbalize(report, repo_name, repo_type)

    else:
        raise NotImplementedError()

    return verbalized_explanation
