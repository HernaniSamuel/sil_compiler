from .utils import ends_with_branch


def generate_if(self, stmt):
    """
    Generates SPIR-V code for an if-else statement.

    Structure:
        if (cond) {
            then_body
        } else {
            else_body
        }

    Uses:
        OpSelectionMerge
        OpBranchConditional
        Basic blocks for then, else (optional), and merge.

    Args:
        stmt (sil_ast.If): The parsed AST node representing the if-statement.

    Returns:
        list[str]: SPIR-V instructions for the conditional block.
    """
    result = []

    then_label = self.new_id()
    else_label = self.new_id() if stmt.else_body else None
    merge_label = self.new_id()

    # Generate condition evaluation
    cond_code, cond_id, _ = self.generate_expr(stmt.condition)
    result.extend(cond_code)

    # Selection merge instruction
    result.append(f"OpSelectionMerge {merge_label} None")
    if else_label:
        result.append(f"OpBranchConditional {cond_id} {then_label} {else_label}")
    else:
        result.append(f"OpBranchConditional {cond_id} {then_label} {merge_label}")

    # Then block
    result.append(f"{then_label} = OpLabel")
    for s in stmt.then_body:
        result.extend(self.generate_stmt(s))

    if not ends_with_branch(result):
        result.append(f"OpBranch {merge_label}")

    # Else block (optional)
    if stmt.else_body:
        result.append(f"{else_label} = OpLabel")
        for s in stmt.else_body:
            result.extend(self.generate_stmt(s))
        if not ends_with_branch(result):
            result.append(f"OpBranch {merge_label}")

    # Merge block
    result.append(f"{merge_label} = OpLabel")
    return result


def generate_loop(self, stmt):
    """
    Generates SPIR-V code for an infinite loop.

    Structure:
        loop {
            body
        }

    Implements:
        OpLoopMerge
        OpBranch to loop condition
        Separate continue and merge blocks

    Args:
        stmt (sil_ast.Loop): The parsed loop block.

    Returns:
        list[str]: SPIR-V instructions for the loop structure.
    """
    merge = self.new_id()
    continue_ = self.new_id()
    cond = self.new_id()
    body = self.new_id()
    header = self.new_id()

    # Save and replace break target for nested breaks
    prev_break_target = getattr(self, 'break_target', None)
    self.break_target = merge

    result = []

    # Header block
    result.append(f"{header} = OpLabel")
    result.append(f"OpLoopMerge {merge} {continue_} None")
    result.append(f"OpBranch {cond}")

    # Condition block (currently unconditional)
    result.append(f"{cond} = OpLabel")
    result.append(f"OpBranch {body}")

    # Body block
    result.append(f"{body} = OpLabel")
    loop_body = []
    for s in stmt.body:
        loop_body.extend(self.generate_stmt(s))

    if not ends_with_branch(loop_body):
        loop_body.append(f"OpBranch {continue_}")
    result.extend(loop_body)

    # Continue block
    result.append(f"{continue_} = OpLabel")
    result.append(f"OpBranch {cond}")

    # Merge block (loop exit)
    result.append(f"{merge} = OpLabel")

    # Restore previous break target
    self.break_target = prev_break_target

    return result
