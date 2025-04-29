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
        self.module_types = []

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
        bool_type = self.new_id()
        uint_type = self.new_id()
        float_type = self.new_id()

        self.type_ids['int'] = uint_type
        self.type_ids['void'] = void_type
        self.type_ids['bool'] = bool_type
        self.type_ids['uint'] = uint_type
        self.type_ids['float'] = float_type

        types.append(f"{void_type} = OpTypeVoid")
        types.append(f"{bool_type} = OpTypeBool")
        types.append(f"{uint_type} = OpTypeInt 32 0")
        types.append(f"{float_type} = OpTypeFloat 32")

        # Ponteiros CrossWorkgroup
        ptr_cross_uint = self.new_id()
        self.type_ids['ptr_cross_uint'] = ptr_cross_uint
        types.append(f"{ptr_cross_uint} = OpTypePointer CrossWorkgroup {self.type_ids['uint']}")

        ptr_cross_float = self.new_id()
        self.type_ids['ptr_cross_float'] = ptr_cross_float
        types.append(f"{ptr_cross_float} = OpTypePointer CrossWorkgroup {self.type_ids['float']}")

        ptr_cross_bool = self.new_id()
        self.type_ids['ptr_cross_bool'] = ptr_cross_bool
        types.append(f"{ptr_cross_bool} = OpTypePointer CrossWorkgroup {self.type_ids['bool']}")

        # Ponteiros Function
        ptr_func_uint = self.new_id()
        self.type_ids['ptr_func_uint'] = ptr_func_uint
        types.append(f"{ptr_func_uint} = OpTypePointer Function {self.type_ids['uint']}")

        ptr_func_float = self.new_id()
        self.type_ids['ptr_func_float'] = ptr_func_float
        types.append(f"{ptr_func_float} = OpTypePointer Function {self.type_ids['float']}")

        ptr_func_bool = self.new_id()
        self.type_ids['ptr_func_bool'] = ptr_func_bool
        types.append(f"{ptr_func_bool} = OpTypePointer Function {self.type_ids['bool']}")

        for node in ast_tree:
            if isinstance(node, sil_ast.Kernel):
                fid = self.new_id()
                self.kernel_func_ids[node.name] = fid

                # Agora a lista de tipos para parâmetros está correta
                param_types = [self.type_ids['ptr_cross_' + p.param_type] for p in node.params]
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
        result.extend(self.module_types)
        result.extend(list(self.constants.values()))
        result.extend(functions)

        return "\n".join(result)

    def get_constant(self, value):
        value_str = str(value)
        if value_str in self.constants:
            return self.constants[value_str].split('=')[0].strip()
        const_id = self.new_id()
        if isinstance(value, int):
            base_type = self.type_ids['uint']  # sempre unsigned agora
        else:
            base_type = self.type_ids['float']
        self.constants[value_str] = f"{const_id} = OpConstant {base_type} {value}"

        return const_id

    def generate_kernel(self, node):
        result = []
        fid = self.kernel_func_ids[node.name]
        fn_type = self.func_type_ids[node.name]

        result.append(f"{fid} = OpFunction {self.type_ids['void']} None {fn_type}")

        self.param_ids.clear()
        self.var_ids.clear()

        for p in node.params:
            # Corrigido: usar o ponteiro certo de acordo com o tipo do parâmetro
            ptr_type = self.type_ids.get('ptr_cross_' + p.param_type)
            if not ptr_type:
                raise Exception(f"No CrossWorkgroup pointer type for {p.param_type}")
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
            result.extend(self.generate_stmt(stmt))

        if not (node.body and isinstance(node.body[-1], sil_ast.Return)):
            result.append("OpReturn")

        result.append("OpFunctionEnd")

        return result

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
        result = []

        if isinstance(stmt, sil_ast.Return):
            result.append("OpReturn")
        elif isinstance(stmt, sil_ast.Assign):
            target_ptr, _ = self.var_ids.get(stmt.name) or self.param_ids.get(stmt.name)
            if target_ptr is None:
                raise Exception(f"Variable or parameter not found: {stmt.name}")
            value_code, value_id, _ = self.generate_expr(stmt.value)
            result.extend(value_code)
            result.append(f"OpStore {target_ptr} {value_id}")
        elif isinstance(stmt, sil_ast.If):
            result.extend(self.generate_if(stmt))
        else:
            raise Exception(f"Unsupported statement type: {type(stmt)}")

        return result

    def generate_expr(self, expr):
        result = []

        if isinstance(expr, sil_ast.Literal):
            const_id = self.get_constant(expr.value)
            if isinstance(expr.value, int):
                return result, const_id, 'int'
            elif isinstance(expr.value, float):
                return result, const_id, 'float'

        elif isinstance(expr, sil_ast.Ident):
            if expr.name in self.var_ids:
                var_ptr, var_type = self.var_ids[expr.name]
                result_id = self.new_id()
                result.append(f"{result_id} = OpLoad {self.type_ids[var_type]} {var_ptr}")
                return result, result_id, var_type
            elif expr.name in self.param_ids:
                param_ptr, param_type = self.param_ids[expr.name]
                result_id = self.new_id()
                result.append(f"{result_id} = OpLoad {self.type_ids[param_type]} {param_ptr}")
                return result, result_id, param_type
            else:
                raise Exception(f"Unknown identifier: {expr.name}")

        elif isinstance(expr, sil_ast.BinaryOp):
            left_code, left_id, left_type = self.generate_expr(expr.left)
            right_code, right_id, right_type = self.generate_expr(expr.right)
            result.extend(left_code)
            result.extend(right_code)

            # 🚨 Verificação de tipo antes de gerar a operação!
            if left_type != right_type:
                raise Exception(f"Type mismatch in binary operation: {left_type} vs {right_type}")

            result_id = self.new_id()

            op_map_int = {
                '+': 'OpIAdd', '-': 'OpISub', '*': 'OpIMul', '/': 'OpSDiv', '//': 'OpSDiv',
                '==': 'OpIEqual', '!=': 'OpINotEqual', '<': 'OpSLessThan', '>': 'OpSGreaterThan',
                '<=': 'OpSLessThanEqual', '>=': 'OpSGreaterThanEqual', '&&': 'OpLogicalAnd', '||': 'OpLogicalOr'
            }

            op_map_float = {
                '+': 'OpFAdd', '-': 'OpFSub', '*': 'OpFMul', '/': 'OpFDiv',
                '==': 'OpFOrdEqual', '!=': 'OpFOrdNotEqual', '<': 'OpFOrdLessThan', '>': 'OpFOrdGreaterThan',
                '<=': 'OpFOrdLessThanEqual', '>=': 'OpFOrdGreaterThanEqual'
            }

            comparison_ops = ['==', '!=', '<', '>', '<=', '>=']

            if left_type == 'float':
                instr = op_map_float.get(expr.op)
                if not instr:
                    raise Exception(f"Unsupported float binary operator: {expr.op}")
                result_type = self.type_ids['bool'] if expr.op in comparison_ops else self.type_ids['float']
            else:
                instr = op_map_int.get(expr.op)
                if not instr:
                    raise Exception(f"Unsupported int binary operator: {expr.op}")
                result_type = self.type_ids['bool'] if expr.op in comparison_ops or expr.op in ['&&', '||'] else \
                self.type_ids['int']

            result.append(f"{result_id} = {instr} {result_type} {left_id} {right_id}")
            return result, result_id, 'bool' if expr.op in comparison_ops else left_type

        else:
            raise Exception(f"Unsupported expression type: {type(expr)}")

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
        result.append(f"OpBranch {merge_label}")

        if stmt.else_body:
            result.append(f"{else_label} = OpLabel")
            for s in stmt.else_body:
                result.extend(self.generate_stmt(s))
            result.append(f"OpBranch {merge_label}")

        result.append(f"{merge_label} = OpLabel")

        return result
