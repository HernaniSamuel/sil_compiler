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

        void_type = self.new_id()
        bool_type = self.new_id()
        uint_type = self.new_id()
        float_type = self.new_id()

        self.type_ids['void'] = void_type
        self.type_ids['bool'] = bool_type
        self.type_ids['uint'] = uint_type
        self.type_ids['int'] = uint_type  # int é alias para uint (não duplica tipo)
        self.type_ids['float'] = float_type

        types.append(f"{void_type} = OpTypeVoid")
        types.append(f"{bool_type} = OpTypeBool")
        types.append(f"{uint_type} = OpTypeInt 32 0")  # Só UM unsigned int, para ambos int e uint
        types.append(f"{float_type} = OpTypeFloat 32")

        # Ponteiros CrossWorkgroup
        ptr_cross_int = self.new_id()
        self.type_ids['ptr_cross_int'] = ptr_cross_int
        types.append(f"{ptr_cross_int} = OpTypePointer CrossWorkgroup {self.type_ids['int']}")

        ptr_cross_uint = self.new_id()
        self.type_ids['ptr_cross_uint'] = ptr_cross_uint
        types.append(f"{ptr_cross_uint} = OpTypePointer CrossWorkgroup {self.type_ids['uint']}")

        ptr_cross_float = self.new_id()
        self.type_ids['ptr_cross_float'] = ptr_cross_float
        types.append(f"{ptr_cross_float} = OpTypePointer CrossWorkgroup {self.type_ids['float']}")

        ptr_cross_bool = self.new_id()
        self.type_ids['ptr_cross_bool'] = ptr_cross_bool
        types.append(f"{ptr_cross_bool} = OpTypePointer CrossWorkgroup {self.type_ids['bool']}")

        # Aliases para tipos de ponteiro usados explicitamente
        self.type_ids['ptr_int'] = self.type_ids['ptr_cross_int']
        self.type_ids['ptr_uint'] = self.type_ids['ptr_cross_uint']
        self.type_ids['ptr_float'] = self.type_ids['ptr_cross_float']
        self.type_ids['ptr_bool'] = self.type_ids['ptr_cross_bool']

        # Ponteiros Function
        ptr_func_int = self.new_id()
        self.type_ids['ptr_func_int'] = ptr_func_int
        types.append(f"{ptr_func_int} = OpTypePointer Function {self.type_ids['int']}")

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
                param_types = []
                for p in node.params:
                    if p.param_type.startswith("ptr_"):
                        param_types.append(self.type_ids[p.param_type])
                    else:
                        param_types.append(self.type_ids['ptr_cross_' + p.param_type])

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
            target_ptr_info = self.var_ids.get(stmt.name) or self.param_ids.get(stmt.name)
            if target_ptr_info is None:
                raise Exception(f"Variable or parameter not found: {stmt.name}")

            target_ptr, target_type = target_ptr_info
            value_code, value_id, value_type = self.generate_expr(stmt.value)
            result.extend(value_code)

            # CONVERSÃO bool → uint (se necessário)
            if value_type == 'bool' and (target_type == 'ptr_uint' or target_type == 'uint'):
                conv_id = self.new_id()
                result.append(
                    f"{conv_id} = OpSelect {self.type_ids['uint']} {value_id} {self.get_constant(1)} {self.get_constant(0)}")
                value_id = conv_id
                value_type = 'uint'

            # Handle storing to pointer parameters
            if target_type.startswith('ptr_'):
                if stmt.name in self.param_ids:
                    result.append(f"OpStore {target_ptr} {value_id}")
                else:
                    result.append(f"OpStore {target_ptr} {value_id}")
            else:
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
                return result, const_id, 'uint'  # Alterado para 'uint' ao invés de 'int'
            elif isinstance(expr.value, float):
                return result, const_id, 'float'

        elif isinstance(expr, sil_ast.UnaryOp):
            code, operand_id, operand_type = self.generate_expr(expr.expr)

            if expr.op == '!':
                if operand_type == 'bool':
                    # Convert bool → uint
                    conv_id = self.new_id()
                    code.append(
                        f"{conv_id} = OpSelect {self.type_ids['uint']} {operand_id} {self.get_constant(1)} {self.get_constant(0)}")
                    operand_id = conv_id
                    operand_type = 'uint'

                # Agora faz (1 - x)
                one_const = self.get_constant(1)
                sub_id = self.new_id()
                code.append(f"{sub_id} = OpISub {self.type_ids['uint']} {one_const} {operand_id}")

                # Converte de volta para bool
                result_id = self.new_id()
                code.append(f"{result_id} = OpINotEqual {self.type_ids['bool']} {sub_id} {self.get_constant(0)}")

                return code, result_id, 'bool'

            elif expr.op == '-':
                result_id = self.new_id()
                code.append(f"{result_id} = OpSNegate {self.type_ids[operand_type]} {operand_id}")
                return code, result_id, operand_type
            else:
                raise Exception(f"Unsupported unary operator: {expr.op}")

        elif isinstance(expr, sil_ast.Ident):
            if expr.name in self.var_ids:
                var_ptr, var_type = self.var_ids[expr.name]
                if var_type.startswith('ptr_'):
                    # Se já é ponteiro (ex: ptr_uint), não precisa OpLoad
                    return result, var_ptr, var_type
                else:
                    result_id = self.new_id()
                    result.append(f"{result_id} = OpLoad {self.type_ids[var_type]} {var_ptr}")
                    return result, result_id, var_type

            elif expr.name in self.param_ids:
                param_ptr, param_type = self.param_ids[expr.name]
                if param_type.startswith('ptr_'):
                    # Se já é ponteiro (ex: ptr_uint), não faz OpLoad
                    return result, param_ptr, param_type
                else:
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

            # Se operação é && ou ||, converter uint para bool se necessário
            if expr.op in ['&&', '||']:
                if left_type == 'uint':
                    conv_id = self.new_id()
                    result.append(f"{conv_id} = OpINotEqual {self.type_ids['bool']} {left_id} {self.get_constant(0)}")
                    left_id = conv_id
                    left_type = 'bool'

                if right_type == 'uint':
                    conv_id = self.new_id()
                    result.append(f"{conv_id} = OpINotEqual {self.type_ids['bool']} {right_id} {self.get_constant(0)}")
                    right_id = conv_id
                    right_type = 'bool'

            if left_type != right_type:
                raise Exception(f"Type mismatch in binary operation: {left_type} vs {right_type}")

            result_id = self.new_id()

            op_map_int = {
                '+': 'OpIAdd', '-': 'OpISub', '*': 'OpIMul', '/': 'OpSDiv', '//': 'OpUDiv', '%': 'OpUMod',
                '==': 'OpIEqual', '!=': 'OpINotEqual', '<': 'OpULessThan', '>': 'OpUGreaterThan',
                '<=': 'OpULessThanEqual', '>=': 'OpUGreaterThanEqual', '&&': 'OpLogicalAnd', '||': 'OpLogicalOr'
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
                # Corrigido: usar o tipo correto (uint ao invés de int)
                result_type = self.type_ids['bool'] if expr.op in comparison_ops or expr.op in ['&&', '||'] else \
                    self.type_ids['uint']

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

    def get_constant_false(self):
        if "false" not in self.constants:
            const_id = self.new_id()
            self.constants["false"] = f"{const_id} = OpConstantFalse {self.type_ids['bool']}"
        return self.constants["false"].split('=')[0].strip()
