# generator.py

import sil_ast

class Generator:
    def __init__(self):
        self.next_id = 1
        self.type_ids = {}
        self.var_ids = {}
        self.param_ids = {}
        self.kernel_func_ids = {}
        self.func_type_ids = {}
        self.constants = {}

    def new_id(self):
        id = self.next_id
        self.next_id += 1
        return f"%{id}"

    def generate(self, ast_tree):
        header = ["; SPIR-V", "; Version: 1.0"]
        capabilities = ["OpCapability Kernel"]
        extensions = []
        memory_model = ["OpMemoryModel Logical OpenCL"]
        entry_points = []
        execution_modes = []
        debug = []
        annotations = []
        types = []

        int_type = self.new_id()
        void_type = self.new_id()
        self.type_ids['int'] = int_type
        self.type_ids['void'] = void_type

        types.append(f"{int_type} = OpTypeInt 32 0")
        types.append(f"{void_type} = OpTypeVoid")

        ptr_cross_int = self.new_id()
        self.type_ids['ptr_cross_int'] = ptr_cross_int
        types.append(f"{ptr_cross_int} = OpTypePointer CrossWorkgroup {int_type}")

        ptr_func_int = self.new_id()
        self.type_ids['ptr_func_int'] = ptr_func_int
        types.append(f"{ptr_func_int} = OpTypePointer Function {int_type}")

        for node in ast_tree:
            if isinstance(node, ast.Kernel):
                fid = self.new_id()
                self.kernel_func_ids[node.name] = fid

                param_types = [self.type_ids['ptr_cross_int'] for _ in node.params]
                fn_type = self.new_id()
                self.func_type_ids[node.name] = fn_type

                param_str = ' '.join(param_types)
                types.append(f"{fn_type} = OpTypeFunction {self.type_ids['void']} {param_str}")

                entry_points.append(f"OpEntryPoint Kernel {fid} \"{node.name}\"")

        functions = []
        for node in ast_tree:
            if isinstance(node, sil_ast.Kernel):
                functions.extend(self.generate_kernel(node))

        result = []
        result.extend(header)
        result.extend(capabilities)
        result.extend(extensions)
        result.extend(memory_model)
        result.extend(entry_points)
        result.extend(execution_modes)
        result.extend(debug)
        result.extend(annotations)
        result.extend(types)
        result.extend(list(self.constants.values()))
        result.extend(functions)

        return "\n".join(result)

    def get_constant(self, value):
        value_str = str(value)
        if value_str in self.constants:
            return value_str
        const_id = self.new_id()
        int_type = self.type_ids['int']
        self.constants[value_str] = f"{const_id} = OpConstant {int_type} {value}"
        return const_id

    def generate_kernel(self, node):
        result = []
        fid = self.kernel_func_ids[node.name]
        fn_type = self.func_type_ids[node.name]

        result.append(f"{fid} = OpFunction {self.type_ids['void']} None {fn_type}")

        self.param_ids.clear()
        self.var_ids.clear()

        for p in node.params:
            pid = self.new_id()
            result.append(f"{pid} = OpFunctionParameter {self.type_ids['ptr_cross_int']}")
            self.param_ids[p.name] = pid

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
            result.extend(self.generate_stmt(stmt))

        if not (node.body and isinstance(node.body[-1], ast.Return)):
            result.append("OpReturn")

        result.append("OpFunctionEnd")

        return result

    def generate_var_only(self, stmt):
        result = []
        ptr_type = self.type_ids.get('ptr_func_' + stmt.var_type)
        if not ptr_type:
            raise Exception(f"Pointer type not found for: {stmt.var_type}")
        var_id = self.new_id()
        result.append(f"{var_id} = OpVariable {ptr_type} Function")
        self.var_ids[stmt.name] = var_id
        return result

    def generate_stmt(self, stmt):
        result = []

        if isinstance(stmt, sil_ast.Return):
            result.append("OpReturn")
        elif isinstance(stmt, ast.Assign):
            target_ptr = self.var_ids.get(stmt.name) or self.param_ids.get(stmt.name)
            if target_ptr is None:
                raise Exception(f"Variable or parameter not found: {stmt.name}")
            value_code, value_id = self.generate_expr(stmt.value)
            result.extend(value_code)
            result.append(f"OpStore {target_ptr} {value_id}")
        else:
            raise Exception(f"Unsupported statement type: {type(stmt)}")

        return result

    def generate_expr(self, expr):
        result = []

        if isinstance(expr, sil_ast.Literal):
            const_id = self.get_constant(expr.value)
            return result, const_id

        elif isinstance(expr, ast.Ident):
            if expr.name in self.var_ids:
                var_ptr = self.var_ids[expr.name]
                result_id = self.new_id()
                result.append(f"{result_id} = OpLoad {self.type_ids['int']} {var_ptr}")
                return result, result_id
            elif expr.name in self.param_ids:
                param_ptr = self.param_ids[expr.name]
                result_id = self.new_id()
                result.append(f"{result_id} = OpLoad {self.type_ids['int']} {param_ptr}")
                return result, result_id
            else:
                raise Exception(f"Unknown identifier: {expr.name}")

        elif isinstance(expr, sil_ast.BinaryOp):
            left_code, left_id = self.generate_expr(expr.left)
            right_code, right_id = self.generate_expr(expr.right)
            result.extend(left_code)
            result.extend(right_code)

            result_id = self.new_id()
            op_map = {'+': 'OpIAdd', '-': 'OpISub', '*': 'OpIMul', '/': 'OpSDiv'}
            instr = op_map.get(expr.op)
            if not instr:
                raise Exception(f"Unsupported binary operator: {expr.op}")
            result.append(f"{result_id} = {instr} {self.type_ids['int']} {left_id} {right_id}")
            return result, result_id

        else:
            raise Exception(f"Unsupported expression type: {type(expr)}")
