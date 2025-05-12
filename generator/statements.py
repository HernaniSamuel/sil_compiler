import sil_ast


def generate_var_only(self, stmt):
    """
    Allocates space for a local (function-scope) variable.

    Args:
        stmt (sil_ast.VarDecl): Variable declaration node.

    Returns:
        list[str]: SPIR-V instructions to declare the variable.
    """
    result = []

    # Normalize type to avoid nested pointers like ptr_func_ptr_uint
    base_type = stmt.var_type
    if base_type.startswith("ptr_"):
        base_type = base_type[len("ptr_"):]

    ptr_type = self.type_ids.get(f'ptr_func_{base_type}')
    if not ptr_type:
        raise Exception(f"Unknown pointer type for {stmt.var_type}")

    var_id = self.new_id()
    result.append(f"{var_id} = OpVariable {ptr_type} Function")
    self.var_ids[stmt.name] = (var_id, stmt.var_type)
    return result


def generate_stmt(self, stmt):
    """
    Dispatches generation of SPIR-V code based on statement type.

    Args:
        stmt (AST node): A statement node from sil_ast.

    Returns:
        list[str]: Generated SPIR-V instructions.
    """
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
    """
    Generates a return instruction. If a value is returned,
    generates code for the expression first.
    """
    if hasattr(stmt, 'value') and stmt.value:
        result = []
        value_code, value_id, value_type = self.generate_expr(stmt.value)
        result.extend(value_code)
        return result + ["OpReturn"]
    return ["OpReturn"]


def _generate_assign(self, stmt):
    """
    Generates code for assignments to variables or pointers.

    Handles:
    - Assignments to declared variables
    - Assignments to dereferenced pointers
    - Constant initialization
    - Type coercion (e.g., bool → uint)
    """
    result = []

    # Determine assignment target
    if isinstance(stmt.target, sil_ast.Ident):
        # Possibly a constant being initialized
        if stmt.target.name in self.constants and self.constants[stmt.target.name] is None:
            value_code, value_id, value_type = self.generate_expr(stmt.value)
            result.extend(value_code)
            self.constants[stmt.target.name] = value_id
            self.constant_types[stmt.target.name] = value_type
            return result

        # Normal variable or parameter assignment
        target_ptr_info = self.var_ids.get(stmt.target.name) or self.param_ids.get(stmt.target.name)
        if target_ptr_info is None:
            raise Exception(f"Variable or parameter not found: {stmt.target.name}")
        target_ptr, target_type = target_ptr_info

    elif isinstance(stmt.target, sil_ast.Dereference):
        code, target_ptr, target_type = self.generate_expr(stmt.target.expr)
        result.extend(code)

        if not target_type.startswith("ptr_"):
            raise Exception(f"Dereferencing non-pointer type: {target_type}")

        # Strip 'ptr_' prefix to get actual value type
        target_type = target_type[len("ptr_"):]

    else:
        raise Exception(f"Unsupported assignment target type: {type(stmt.target)}")

    # Generate code for RHS expression
    value_code, value_id, value_type = self.generate_expr(stmt.value)
    result.extend(value_code)

    # Handle bool → uint coercion (e.g., storing a bool into a uint slot)
    if value_type == 'bool' and (target_type == 'ptr_uint' or target_type == 'uint'):
        conv_id = self.new_id()
        result.append(
            f"{conv_id} = OpSelect {self.type_ids['uint']} {value_id} "
            f"{self.get_constant(1)} {self.get_constant(0)}"
        )
        value_id = conv_id
        value_type = 'uint'

    result.append(f"OpStore {target_ptr} {value_id}")
    return result


def _generate_break(self, stmt):
    """
    Emits a branch to the current break target.
    Used inside loops.
    """
    if not hasattr(self, 'break_target') or self.break_target is None:
        raise Exception("Break used outside of a loop")

    return [f"OpBranch {self.break_target}"]


def generate_const_decl(self, stmt):
    """
    Handles constant declarations.

    If the value is a literal, emits an OpConstant immediately.
    Otherwise, defers resolution to the assign phase.

    Args:
        stmt (sil_ast.ConstDecl): The constant declaration node.

    Returns:
        list[str]: SPIR-V code (usually empty, unless literal).
    """
    if isinstance(stmt.value, sil_ast.Literal):
        value = stmt.value.value
        const_type = 'uint' if isinstance(value, int) else 'float'
        const_id = self.get_constant(value)

        self.constants[stmt.name] = const_id
        self.constant_types[stmt.name] = const_type

    elif isinstance(stmt.value, (sil_ast.Ident, sil_ast.BinaryOp)):
        self.constants[stmt.name] = None  # will resolve later
        self.constant_types[stmt.name] = getattr(stmt, 'var_type', 'uint')

    else:
        self.constants[stmt.name] = None
        self.constant_types[stmt.name] = getattr(stmt, 'var_type', 'uint')

    return []
