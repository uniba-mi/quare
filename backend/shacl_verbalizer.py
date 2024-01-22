def verbalize(message: str) -> list[str]:
    verbalized_explanation = []

    splitlines = message.splitlines()

    for index, line in enumerate(splitlines):
        # For NodeConstraintComponent, there is a more specific violation in the details, so skip the general one.
        if ("Constraint Violation" in line) & ("NodeConstraintComponent" not in line):
            violation_message = extract_violation_message(splitlines[index:])
            verbalized_explanation.append(violation_message)
    return verbalized_explanation


def extract_violation_message(lines: list[str]) -> str:
    for line in lines:
        if "Message" in line:
            return line.split("Message: ")[1].strip()
