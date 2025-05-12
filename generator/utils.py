def ends_with_branch(code):
    """
    Checks whether a list of SPIR-V instruction lines ends with a branching instruction.

    Used to ensure that blocks are properly terminated before inserting a new label.

    Args:
        code (list of str): A list of SPIR-V instruction lines.

    Returns:
        bool: True if the last line is a branch or return instruction, False otherwise.
    """
    if not code:
        return False

    return (
        code[-1].startswith("OpBranch")
        or code[-1].startswith("OpReturn")
        or code[-1].startswith("OpBranchConditional")
    )
