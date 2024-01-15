#!/usr/bin/env python3

import logging
from time import perf_counter

import shacl_validator

logger = logging.getLogger(__name__)


def run_validator(github_access_token: str = "", repo_name: str = "", repo_type: str = "") \
        -> tuple[int, int | None, str]:
    time_start = perf_counter()

    return_code, number_of_violations, report = shacl_validator.validate_repo_against_specs(
        github_access_token, repo_name, repo_type)

    logger.info(return_code)

    # interpret boolean as number
    return_code = 0 if return_code else 1

    time_elapsed = perf_counter() - time_start

    logger.info("Validating the %s repository against the %s project type took %s seconds!",
                repo_name, repo_type, '{:f}'.format(time_elapsed))

    return return_code, number_of_violations, report


def get_project_type_specifications() -> dict[str, dict[str, list[str]]]:
    return {"projectTypeSpecifications": shacl_validator.get_project_type_specifications()}
