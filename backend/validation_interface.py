#!/usr/bin/env python3

import logging
from subprocess import run
from time import perf_counter

import owl_validator
import shacl_validator

logger = logging.getLogger(__name__)


def run_validator(github_access_token: str = "", repo_name: str = "", repo_type: str = "", method: str = "") \
        -> tuple[int, int | None, str]:
    number_of_violations = None
    time_start = perf_counter()

    if method == "owl":

        cmd = ["python3", "owl_validator.py", "--github_access_token", github_access_token,
               "--repo_name", repo_name, "--expected_type", repo_type]

        try:
            output = run(cmd, capture_output=True)
            return_code = output.returncode
        except Exception as e:
            logger.exception(e)

        if return_code:
            stderr = output.stderr.decode()

            stderr = stderr.split("Explanation(s):")[1].strip()
            report = stderr.split("\n\n\n")[0]

    elif method == "shacl":

        return_code, number_of_violations, report = shacl_validator.validate_repo_against_specs(
            github_access_token, repo_name, repo_type)

        logger.info(return_code)

        # interpret boolean as number
        return_code = 0 if return_code else 1

    else:
        raise NotImplementedError()

    time_elapsed = perf_counter() - time_start

    logger.info("Validating the %s repository against the %s project type using the %s approach took %s seconds!",
                repo_name, repo_type, method.upper(), '{:f}'.format(time_elapsed))

    return return_code, number_of_violations, report


def get_project_type_specifications():
    project_type_specifcations = {
        "projectTypeSpecifications": {
            "owl": owl_validator.get_project_type_specifications(),
            "shacl": shacl_validator.get_project_type_specifications()
        }
    }

    return project_type_specifcations
