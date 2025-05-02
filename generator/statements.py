import sil_ast

def generate_var_only(self, stmt):
    result = []
    ptr_type = self.type_ids.get('ptr_func_' + stmt.var_type)
    if not ptr_type:
        raise Exception(f"Unknown pointer type for {stmt.var_type}")
    var_id = self.new_id()
    result.append(f"{var_id} = OpVariable {ptr_type} Function")
    self.var_ids[stmt.name] = (var_id, stmt.var_type)
    return result


def generate_stmt(self, stmt):
    if isinstance(stmt, sil_ast.Return):
        return _generate_return(self, stmt)
    elif isinstance(stmt, sil_ast.Assign):
        return _generate_assign(self, stmt)
    elif isinstance(stmt, sil_ast.If):
        return self.generate_if(stmt)
    elif isinstance(stmt, sil_ast.Loop):
        return self.generate_loop(stmt)
    elif isinstance(stmt, sil_ast.Break):
        return _generate_break(self, stmt)
    else:
        raise Exception(f"Unsupported statement type: {type(stmt)}")

def _generate_return(self, stmt):
    return ["OpReturn"]

def _generate_assign(self, stmt):
    result = []

    target_ptr_info = self.var_ids.get(stmt.name) or self.param_ids.get(stmt.name)
    if target_ptr_info is None:
        raise Exception(f"Variable or parameter not found: {stmt.name}")

    target_ptr, target_type = target_ptr_info
    value_code, value_id, value_type = self.generate_expr(stmt.value)
    result.extend(value_code)

    if value_type == 'bool' and (target_type == 'ptr_uint' or target_type == 'uint'):
        conv_id = self.new_id()
        result.append(
            f"{conv_id} = OpSelect {self.type_ids['uint']} {value_id} {self.get_constant(1)} {self.get_constant(0)}")
        value_id = conv_id
        value_type = 'uint'

    result.append(f"OpStore {target_ptr} {value_id}")
    return result

def _generate_break(self, stmt):
    if not hasattr(self, 'break_target') or self.break_target is None:
        raise Exception("Break usado fora de um loop")
    return [f"OpBranch {self.break_target}"]
