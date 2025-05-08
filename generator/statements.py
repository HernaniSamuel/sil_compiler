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
    elif isinstance(stmt, sil_ast.ConstDecl):
        return generate_const_decl(self, stmt)
    else:
        raise Exception(f"Unsupported statement type: {type(stmt)}")


def _generate_return(self, stmt):
    # If there's a return value, generate code for it
    if hasattr(stmt, 'value') and stmt.value:
        result = []
        value_code, value_id, value_type = self.generate_expr(stmt.value)
        result.extend(value_code)
        return result + ["OpReturn"]
    return ["OpReturn"]


def _generate_assign(self, stmt):
    result = []

    # Check if we're assigning to a const that was declared previously
    if stmt.name in self.constants and self.constants[stmt.name] is None:
        # This is a constant that was declared but not initialized yet
        value_code, value_id, value_type = self.generate_expr(stmt.value)
        result.extend(value_code)

        # Store the constant value ID
        self.constants[stmt.name] = value_id

        # And also store the constant value type
        self.constant_types[stmt.name] = value_type

        return result

    # Regular variable assignment
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


def generate_const_decl(self, stmt):
    if isinstance(stmt.value, sil_ast.Literal):
        # We're handling a direct literal value
        value = stmt.value.value
        const_type = 'uint' if isinstance(value, int) else 'float'

        # Get the constant ID for this value
        const_id = self.get_constant(value)

        # Store the constant ID with its name
        self.constants[stmt.name] = const_id

        # Store the constant type
        self.constant_types[stmt.name] = const_type
    elif isinstance(stmt.value, sil_ast.Ident) or isinstance(stmt.value, sil_ast.BinaryOp):
        # For expressions that need to be evaluated, we'll handle them during later stages
        # For now, mark this constant as "not initialized yet"
        self.constants[stmt.name] = None
        # Use the var_type attribute instead of value_type
        self.constant_types[stmt.name] = getattr(stmt, 'var_type', 'uint')
    else:
        # Other expression types that we'll evaluate later
        self.constants[stmt.name] = None
        # Use the var_type attribute instead of value_type
        self.constant_types[stmt.name] = getattr(stmt, 'var_type', 'uint')

    return []