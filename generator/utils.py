def ends_with_branch(code):
    if not code:
        return False
    return code[-1].startswith("OpBranch") or code[-1].startswith("OpReturn") or code[-1].startswith(
        "OpBranchConditional")