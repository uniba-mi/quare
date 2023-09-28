#!/usr/bin/env python3

import logging
from subprocess import run
from time import perf_counter

import owl_validator
import shacl_validator

logger = logging.getLogger(__name__)


def verbalize_pellet_explanation(explanation, repo_name, repo_type):
    split_repo_name = repo_name.split("/")[1]
    candidate_props = []

    for line in explanation.splitlines():
        splitline = line.split(" ")

        if split_repo_name in splitline and repo_type in splitline:
            pass
        elif split_repo_name in splitline:
            candidate_props.append(
                splitline[splitline.index(split_repo_name) + 1])

    affected_constraints = {}
    for line in explanation.splitlines():
        splitline = line.split(" ")

        if repo_type in splitline or "and" in splitline:
            for index, elem in enumerate(splitline):
                if elem in candidate_props:
                    affected_constraints[elem] = splitline[index+1:]

    verbalized_explanation = f"{repo_name} does not comply with the quality criteria of {repo_type}:\n"

    for violation_property in candidate_props:
        violation_type = affected_constraints[violation_property][0]

        if violation_type == "some":
            verbalized_explanation += f"- It seems like there is no {violation_property}.\n"
        elif violation_type == "only":
            verbalized_explanation += f"- It seems like a {violation_property} points to a disallowed object.\n"
        elif violation_type == "min":
            verbalized_explanation += f"- It seems like there are too few {violation_property} properties.\n"
        elif violation_type == "max":
            verbalized_explanation += f"- It seems like there are too many {violation_property} properties.\n"
        elif violation_type == "exactly":
            verbalized_explanation += f"- It seems like there is the wrong number of {violation_property} properties.\n"
        elif violation_type == "value":
            verbalized_explanation += f"- It seems like a {violation_property} property does not have the correct value.\n"
        elif violation_type == "has_self":
            verbalized_explanation += f"- It seems like the {violation_property} property is not reflexive.\n"
        else:
            verbalized_explanation += f"- There seems to be a problem with the {violation_property} property.\n"

    return verbalized_explanation


def verbalize_shacl_explanation(explanation, repo_name, repo_type):
    splitlines = explanation.splitlines()
    violations = []

    for index, line in enumerate(splitlines):
        if "Constraint Violation" in line:
            splitline = line.split(" ")
            violation_type = splitline[3]

            if "Qualified" in violation_type:
                violation_type = splitline[4].split("#")[1].replace("):", "")

            for other_line in splitlines[index:]:
                if "Result Path" in other_line:
                    result_path_line = other_line
                    break

            violation_property = result_path_line.split("Result Path: ")[
                1].strip()
            violations.append((violation_type, violation_property))

    verbalized_explanation = f"{repo_name} does not comply with the quality criteria of {repo_type}:\n"

    for violation_type, violation_property in violations:

        if violation_type == "MinCountConstraintComponent":
            verbalized_explanation += f"- It seems like there are too few {violation_property} properties.\n"
        elif violation_type == "MaxCountConstraintComponent":
            verbalized_explanation += f"- It seems like there are too many {violation_property} properties.\n"
        elif violation_type == "PatternConstraintComponent":
            verbalized_explanation += f"- It seems like a {violation_property} property does not have the correct value.\n"
        elif violation_type == "QualifiedMinCountConstraintComponent":
            verbalized_explanation += f"- It seems like there are too few nodes at the end of the path {violation_property} with the correct value.\n"
        elif violation_type == "QualifiedMaxCountConstraintComponent":
            verbalized_explanation += f"- It seems like there are too many nodes at the end of the path {violation_property} with the correct value.\n"
        else:
            verbalized_explanation += f"- It seems like the {violation_property} property does not comply with {violation_type}.\n"

    return verbalized_explanation


def run_validator(github_access_token="", repo_name="", repo_type="", method=""):

    results = {"repoName": repo_name, "returnCode": "",
               "message": "", "verbalized": ""}

    time_start = perf_counter()

    if method == "owl":

        cmd = ["python3", "owl_validator.py", "--github_access_token", github_access_token,
               "--repo_name", repo_name, "--expected_type", repo_type]

        try:
            output = run(cmd, capture_output=True)
            results["returnCode"] = output.returncode
        except Exception as e:
            logger.exception(e)
            

        if results["returnCode"]:
            stderr = output.stderr.decode()

            stderr = stderr.split("Explanation(s):")[1].strip()
            explanation = stderr.split("\n\n\n")[0]

            results["message"] = explanation
            results["verbalized"] = verbalize_pellet_explanation(
                explanation, repo_name, repo_type)

    elif method == "shacl":

        returncode, explanation = shacl_validator.test_repo_against_specs(
            github_access_token, repo_name, repo_type)

        results["returnCode"] = 0 if returncode else 1

        if results["returnCode"]:
            results["message"] = explanation
            results["verbalized"] = verbalize_shacl_explanation(
                explanation, repo_name, repo_type)

    else:
        raise NotImplementedError()

    time_elapsed = perf_counter() - time_start

    logger.info("Validating the %s repository against the %s project type using the %s approach took %s seconds!",
                repo_name, repo_type, method.upper(), '{:f}'.format(time_elapsed))

    return results


def get_project_type_specifcations():

    project_type_specifcations = {"owl": owl_validator.get_project_type_specifcations(),
                                  "shacl": shacl_validator.get_project_type_specifcations()}

    return project_type_specifcations


if __name__ == "__main__":
    run_validator(
        "", "uniba-mi/blender_lernapp", "TeachingTool", "shacl")

    run_validator(
        "", "uniba-mi/rdftex", "FinishedResearchProject", "shacl")
