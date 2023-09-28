def verbalize(explanation, repo_name, repo_type):
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