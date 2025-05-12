import sil_ast
from .utils import ends_with_branch


def collect_entry_points_and_function_types(self, ast_tree):
    """
    Collects kernel entry points and builds their function types.

    Args:
        ast_tree (list): List of top-level AST nodes.

    Returns:
        tuple:
            - entry_points (list[str]): OpEntryPoint declarations.
            - func_types (list[str]): OpTypeFunction declarations.
    """
    entry_points = []
    func_types = []

    for node in ast_tree:
        if isinstance(node, sil_ast.Kernel):
            fid = self.new_id()
            self.kernel_func_ids[node.name] = fid

            # Gather parameter types
            param_types = []
            for p in node.params:
                if p.param_type.startswith("ptr_"):
                    param_types.append(self.type_ids[p.param_type])
                else:
                    param_types.append(self.type_ids['ptr_cross_' + p.param_type])

            fn_type = self.new_id()
            self.func_type_ids[node.name] = fn_type
            param_str = ' '.join(param_types)

            func_types.append(f"{fn_type} = OpTypeFunction {self.type_ids['void']} {param_str}")
            entry_points.append(f"OpEntryPoint Kernel {fid} \"{node.name}\"")

    return entry_points, func_types


def generate_kernel(self, node):
    """
    Generates SPIR-V code for a kernel function.

    Args:
        node (sil_ast.Kernel): Kernel AST node.

    Returns:
        list[str]: SPIR-V instructions for the kernel.
    """
    result = []

    fid = self.kernel_func_ids[node.name]
    fn_type = self.func_type_ids[node.name]

    result.append(f"{fid} = OpFunction {self.type_ids['void']} None {fn_type}")

    self.param_ids.clear()
    self.var_ids.clear()

    # Generate OpFunctionParameter instructions for each kernel parameter
    for p in node.params:
        if p.param_type.startswith("ptr_"):
            ptr_type = self.type_ids[p.param_type]
        else:
            ptr_type = self.type_ids['ptr_cross_' + p.param_type]

        if not ptr_type:
            raise Exception(f"Unknown pointer type for {p.param_type}")

        pid = self.new_id()
        result.append(f"{pid} = OpFunctionParameter {ptr_type}")
        self.param_ids[p.name] = (pid, p.param_type)

    # Entry label
    label = self.new_id()
    result.append(f"{label} = OpLabel")

    # Organize statements
    var_decls = []
    const_decls = []
    other_stmts = []

    for stmt in node.body:
        if isinstance(stmt, sil_ast.VarDecl):
            var_decls.append(stmt)
        elif isinstance(stmt, sil_ast.ConstDecl):
            const_decls.append(stmt)
        else:
            other_stmts.append(stmt)

    # 1. Emit constant declarations with literal values
    for const in const_decls:
        if isinstance(const.value, sil_ast.Literal):
            const_code = self.generate_stmt(const)
            if const_code:
                result.extend(const_code)

    # 2. Emit local variable declarations (without initialization)
    for var in var_decls:
        result.extend(self.generate_var_only(var))

    # 3. Emit initialization code for variables
    for var in var_decls:
        if var.value:
            assign = sil_ast.Assign(sil_ast.Ident(var.name), var.value)
            result.extend(self.generate_stmt(assign))

    # 4. Emit initialization for constants referencing expressions or variables
    for const in const_decls:
        if not isinstance(const.value, sil_ast.Literal):
            assign = sil_ast.Assign(name=const.name, value=const.value)
            assign_code = self.generate_stmt(assign)
            if assign_code:
                result.extend(assign_code)

    # 5. Emit remaining executable statements
    for stmt in other_stmts:
        stmt_code = self.generate_stmt(stmt)
        if stmt_code is None:
            raise Exception(f"generate_stmt returned None for statement: {stmt}")

        # Ensure previous block ends with branch or return
        if not ends_with_branch(result):
            if stmt_code[0].strip().endswith("= OpLabel"):
                label_id = stmt_code[0].split('=')[0].strip()
                result.append(f"OpBranch {label_id}")
            else:
                label_id = self.new_id()
                result.append(f"OpBranch {label_id}")
                result.append(f"{label_id} = OpLabel")

        result.extend(stmt_code)

    # Ensure function ends with return
    if not (node.body and isinstance(node.body[-1], sil_ast.Return)):
        result.append("OpReturn")

    result.append("OpFunctionEnd")
    return result
