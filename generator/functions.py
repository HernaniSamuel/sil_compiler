import sil_ast
from .utils import ends_with_branch


def collect_entry_points_and_function_types(self, ast_tree):
    entry_points = []
    func_types = []
    for node in ast_tree:
        if isinstance(node, sil_ast.Kernel):
            fid = self.new_id()
            self.kernel_func_ids[node.name] = fid

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
    result = []
    fid = self.kernel_func_ids[node.name]
    fn_type = self.func_type_ids[node.name]

    result.append(f"{fid} = OpFunction {self.type_ids['void']} None {fn_type}")

    self.param_ids.clear()
    self.var_ids.clear()

    for p in node.params:
        # Corrigido: usar o ponteiro certo de acordo com o tipo do parâmetro
        if p.param_type.startswith("ptr_"):
            ptr_type = self.type_ids[p.param_type]
        else:
            ptr_type = self.type_ids['ptr_cross_' + p.param_type]

        if not ptr_type:
            raise Exception(f"Unknown pointer type for {p.param_type}")

        pid = self.new_id()
        result.append(f"{pid} = OpFunctionParameter {ptr_type}")
        self.param_ids[p.name] = (pid, p.param_type)

    label = self.new_id()
    result.append(f"{label} = OpLabel")

    var_decls = []
    other_stmts = []

    for stmt in node.body:
        if isinstance(stmt, sil_ast.VarDecl):
            var_decls.append(stmt)
        else:
            other_stmts.append(stmt)

    for var in var_decls:
        result.extend(self.generate_var_only(var))

    for var in var_decls:
        if var.value:
            assign = sil_ast.Assign(name=var.name, value=var.value)
            result.extend(self.generate_stmt(assign))

    for stmt in other_stmts:
        stmt_code = self.generate_stmt(stmt)
        if stmt_code is None:
            raise Exception(f"generate_stmt retornou None para stmt: {stmt}")

        # Corrigido: se o próximo começa com OpLabel e não fechamos o anterior, precisa de OpBranch
        if not ends_with_branch(result):
            if stmt_code and stmt_code[0].strip().endswith("= OpLabel"):
                label_id = stmt_code[0].split('=')[0].strip()
                result.append(f"OpBranch {label_id}")
            else:
                # Cria um bloco novo antes do código que não começa com label
                label_id = self.new_id()
                result.append(f"OpBranch {label_id}")
                result.append(f"{label_id} = OpLabel")

        result.extend(stmt_code)

    if not (node.body and isinstance(node.body[-1], sil_ast.Return)):
        result.append("OpReturn")

    result.append("OpFunctionEnd")

    return result
