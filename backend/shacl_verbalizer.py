import re


def verbalize(message: str, repo_name: str, repo_type: str) -> str:
    splitlines = message.splitlines()
    violations = []

    for index, line in enumerate(splitlines):
        # For NodeConstraintComponent, there is a more specific violation in the details, so skip the general one.
        if ("Constraint Violation" in line) & ("NodeConstraintComponent" not in line):
            splitline = line.split(" ")
            violation_type = splitline[3]

            if "Qualified" in violation_type:
                violation_type = splitline[4].split("#")[1].replace("):", "")

            violation_property = extract_violation_property(splitlines[index:], violation_type)
            violations.append((violation_type, violation_property))

    return generate_verbalization_for_violations(repo_name, repo_type, violations)


def extract_violation_property(lines: list[str], violation_type: str) -> str:
    if violation_type not in ["AndConstraintComponent", "OrConstraintComponent", "XoneConstraintComponent"]:
        for other_line in lines:
            if "Result Path" in other_line:
                result_path_line = other_line
                return result_path_line.split("Result Path: ")[1].strip()
    else:
        for other_line in lines:
            if "Message: " in other_line:
                result_path_line = other_line
                violation_property = re.split(r"^\s*Message: Node <.* in", result_path_line)[1].strip()
                violation_property = violation_property.replace("[ sh:node nodeShapes:", "")
                violation_property = violation_property.replace("[ sh:property propertyShapes:", "")
                violation_property = violation_property.replace(" ] ", "")
                return violation_property.removesuffix(" ]")


def generate_verbalization_for_violations(repo_name: str, repo_type: str, violations: list[tuple[str, str]]) -> str:
    verbalized_explanation = f"{repo_name} does not comply with the quality criteria of {repo_type}:\n"
    for violation_type, violation_property in violations:
        match violation_type:
            case "AndConstraintComponent":
                verbalized_explanation += (f"- It seems like not all of these conditions are fulfilled: "
                                           f"{violation_property}.\n")
            case "OrConstraintComponent":
                verbalized_explanation += (f"- It seems like none (not at least one) of these conditions is fulfilled: "
                                           f"{violation_property}.\n")
            case "MinCountConstraintComponent":
                verbalized_explanation += f"- It seems like there are too few {violation_property} properties.\n"
            case "MaxCountConstraintComponent":
                verbalized_explanation += f"- It seems like there are too many {violation_property} properties.\n"
            case "PatternConstraintComponent":
                verbalized_explanation += (f"- It seems like a {violation_property} property does not have the correct "
                                           f"value.\n")
            case "QualifiedMinCountConstraintComponent":
                verbalized_explanation += (f"- It seems like there are too few nodes at the end of the path "
                                           f"{violation_property} with the correct value.\n")
            case "QualifiedMaxCountConstraintComponent":
                verbalized_explanation += (f"- It seems like there are too many nodes at the end of the path "
                                           f"{violation_property} with the correct value.\n")
            case "XoneConstraintComponent":
                verbalized_explanation += (f"- It seems like not exactly one of these conditions is fulfilled: "
                                           f"{violation_property}.\n")
            case _:
                verbalized_explanation += (f"- It seems like the {violation_property} property does not comply with "
                                           f"{violation_type}.\n")
    return verbalized_explanation
