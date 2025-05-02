from .utils import ends_with_branch


def generate_if(self, stmt):
    result = []

    then_label = self.new_id()
    else_label = self.new_id() if stmt.else_body else None
    merge_label = self.new_id()

    cond_code, cond_id, _ = self.generate_expr(stmt.condition)
    result.extend(cond_code)

    result.append(f"OpSelectionMerge {merge_label} None")
    if else_label:
        result.append(f"OpBranchConditional {cond_id} {then_label} {else_label}")
    else:
        result.append(f"OpBranchConditional {cond_id} {then_label} {merge_label}")

    result.append(f"{then_label} = OpLabel")
    for s in stmt.then_body:
        result.extend(self.generate_stmt(s))

    # Verificar se o último statement já é um branch (como um break)
    if not ends_with_branch(result):
        result.append(f"OpBranch {merge_label}")

    if stmt.else_body:
        result.append(f"{else_label} = OpLabel")
        for s in stmt.else_body:
            result.extend(self.generate_stmt(s))

        # Verificar se o último statement já é um branch
        if not ends_with_branch(result):
            result.append(f"OpBranch {merge_label}")

    result.append(f"{merge_label} = OpLabel")

    return result


def generate_loop(self, stmt):
    merge = self.new_id()
    continue_ = self.new_id()
    cond = self.new_id()
    body = self.new_id()
    header = self.new_id()

    prev_break_target = getattr(self, 'break_target', None)
    self.break_target = merge

    result = []

    # Cabeçalho do loop
    result.append(f"{header} = OpLabel")
    result.append(f"OpLoopMerge {merge} {continue_} None")
    result.append(f"OpBranch {cond}")

    # Bloco condicional
    result.append(f"{cond} = OpLabel")
    result.append(f"OpBranch {body}")  # Sempre entra no corpo (sem checagem por enquanto)

    # Corpo do loop
    result.append(f"{body} = OpLabel")
    loop_body = []
    for s in stmt.body:
        loop_body.extend(self.generate_stmt(s))
    if not ends_with_branch(loop_body):
        loop_body.append(f"OpBranch {continue_}")
    result.extend(loop_body)

    # Bloco continue
    result.append(f"{continue_} = OpLabel")
    result.append(f"OpBranch {cond}")

    # Bloco de saída
    result.append(f"{merge} = OpLabel")

    self.break_target = prev_break_target
    return result
