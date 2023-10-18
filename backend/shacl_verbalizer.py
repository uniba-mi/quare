def verbalize(message, repo_name, repo_type):
    splitlines = message.splitlines()
    violations = []

    for index, line in enumerate(splitlines):
        if "Constraint Violation" in line:
            splitline = line.split(" ")
            violation_type = splitline[3]

            if "Qualified" in violation_type:
                violation_type = splitline[4].split("#")[1].replace("):", "")

            # TODO: E.g., a "Constraint Violation in OrConstraintComponent" doesn't have a "Result Path".
            # TODO: Currently, in such cases nothing is appended.
            for other_line in splitlines[index:]:
                if "Result Path" in other_line:
                    result_path_line = other_line
                    violation_property = result_path_line.split("Result Path: ")[1].strip()
                    violations.append((violation_type, violation_property))
                    break

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
