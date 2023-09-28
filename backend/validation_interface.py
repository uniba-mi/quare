#!/usr/bin/env python3

import logging
from subprocess import run
from time import perf_counter

import owl_validator
import shacl_validator

logger = logging.getLogger(__name__)


def run_validator(github_access_token="", repo_name="", repo_type="", method=""):

    time_start = perf_counter()

    if method == "owl":

        cmd = ["python3", "owl_validator.py", "--github_access_token", github_access_token,
               "--repo_name", repo_name, "--expected_type", repo_type]

        try:
            output = run(cmd, capture_output=True)
            returncode = output.returncode
        except Exception as e:
            logger.exception(e)
            

        if returncode:
            stderr = output.stderr.decode()

            stderr = stderr.split("Explanation(s):")[1].strip()
            explanation = stderr.split("\n\n\n")[0]

            message = explanation

    elif method == "shacl":

        returncode, explanation = shacl_validator.test_repo_against_specs(
            github_access_token, repo_name, repo_type)

        returncode = 0 if returncode else 1

        if returncode:
            message = explanation

    else:
        raise NotImplementedError()

    time_elapsed = perf_counter() - time_start

    logger.info("Validating the %s repository against the %s project type using the %s approach took %s seconds!",
                repo_name, repo_type, method.upper(), '{:f}'.format(time_elapsed))

    return returncode, message


def get_project_type_specifcations():

    project_type_specifcations = {"owl": owl_validator.get_project_type_specifcations(),
                                  "shacl": shacl_validator.get_project_type_specifcations()}

    return project_type_specifcations
