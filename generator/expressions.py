import sil_ast


def generate_expr(self, expr):
    if isinstance(expr, sil_ast.Literal):
        return _generate_literal(self, expr)
    elif isinstance(expr, sil_ast.Ident):
        return _generate_ident(self, expr)
    elif isinstance(expr, sil_ast.UnaryOp):
        return _generate_unary(self, expr)
    elif isinstance(expr, sil_ast.BinaryOp):
        return _generate_binary(self, expr)
    elif isinstance(expr, sil_ast.BitwiseExpr):
        return self.generate_expr(expr.expr)
    elif isinstance(expr, sil_ast.CastExpr):
        return _generate_cast(self, expr)
    elif isinstance(expr, sil_ast.Dereference):
        return _generate_dereference(self, expr)
    elif isinstance(expr, sil_ast.AddressOf):
        return _generate_addressof(self, expr)
    else:
        raise Exception(f"Unsupported expression type: {type(expr)}")


def _generate_addressof(self, expr):
    if isinstance(expr.expr, sil_ast.Ident):
        var_info = self.var_ids.get(expr.expr.name) or self.param_ids.get(expr.expr.name)
        if var_info is None:
            raise Exception(f"AddressOf aplicado a variável desconhecida: {expr.expr.name}")
        var_id, var_type = var_info

        if var_type.startswith("ptr_"):
            raise Exception("SPIR-V Kernel não permite ponteiro de ponteiro")

        ptr_type = f"ptr_{var_type}"
        return [], var_id, ptr_type
    else:
        raise Exception("AddressOf só é permitido sobre identificadores simples")


def _generate_literal(self, expr):
    result = []
    const_id = self.get_constant(expr.value)
    if isinstance(expr.value, int):
        return result, const_id, 'uint'
    elif isinstance(expr.value, float):
        return result, const_id, 'float'
    else:
        raise Exception(f"Unsupported literal type: {type(expr.value)}")

def _generate_dereference(self, expr):
    result = []
    code, ptr_id, ptr_type = self.generate_expr(expr.expr)
    result.extend(code)

    if not ptr_type.startswith("ptr_"):
        raise Exception(f"Dereferencing non-pointer type: {ptr_type}")

    val_type = ptr_type[len("ptr_"):]
    result_id = self.new_id()
    result.append(f"{result_id} = OpLoad {self.type_ids[val_type]} {ptr_id}")
    return result, result_id, val_type

def _generate_ident(self, expr):
    result = []

    # First check if it's a constant
    if expr.name in self.constants:
        const_id = self.constants[expr.name]

        # If the constant is not initialized yet, check if it's a variable
        if const_id is None:
            # Try to handle it as a variable reference if possible
            if expr.name in self.var_ids:
                var_ptr, var_type = self.var_ids[expr.name]
                result_id = self.new_id()
                result.append(f"{result_id} = OpLoad {self.type_ids[var_type]} {var_ptr}")

                # Store this as the constant value now
                self.constants[expr.name] = result_id
                self.constant_types[expr.name] = var_type

                return result, result_id, var_type
            else:
                raise Exception(f"Constant used before being fully initialized: {expr.name}")

        # Get the constant type
        const_type = self.constant_types.get(expr.name, 'uint')

        return result, const_id, const_type

    elif expr.name in self.var_ids:
        var_ptr, var_type = self.var_ids[expr.name]
        if var_type.startswith('ptr_'):
            return result, var_ptr, var_type
        else:
            result_id = self.new_id()
            result.append(f"{result_id} = OpLoad {self.type_ids[var_type]} {var_ptr}")
            return result, result_id, var_type

    elif expr.name in self.param_ids:
        param_ptr, param_type = self.param_ids[expr.name]
        if param_type.startswith('ptr_'):
            return result, param_ptr, param_type
        else:
            result_id = self.new_id()
            result.append(f"{result_id} = OpLoad {self.type_ids[param_type]} {param_ptr}")
            return result, result_id, param_type

    else:
        raise Exception(f"Unknown identifier: {expr.name}")


def _generate_unary(self, expr):
    result = []
    code, operand_id, operand_type = self.generate_expr(expr.expr)
    result.extend(code)

    if expr.op == '!':
        if operand_type == 'bool':
            conv_id = self.new_id()
            result.append(
                f"{conv_id} = OpSelect {self.type_ids['uint']} {operand_id} {self.get_constant(1)} {self.get_constant(0)}")
            operand_id = conv_id
            operand_type = 'uint'

        one_const = self.get_constant(1)
        sub_id = self.new_id()
        result.append(f"{sub_id} = OpISub {self.type_ids['uint']} {one_const} {operand_id}")
        result_id = self.new_id()
        result.append(f"{result_id} = OpINotEqual {self.type_ids['bool']} {sub_id} {self.get_constant(0)}")
        return result, result_id, 'bool'

    elif expr.op == '-':
        result_id = self.new_id()
        result.append(f"{result_id} = OpSNegate {self.type_ids[operand_type]} {operand_id}")
        return result, result_id, operand_type

    elif expr.op == '~':
        result_id = self.new_id()
        result.append(f"{result_id} = OpNot {self.type_ids[operand_type]} {operand_id}")
        return result, result_id, operand_type

    else:
        raise Exception(f"Unsupported unary operator: {expr.op}")


def _generate_binary(self, expr):
    result = []
    left_code, left_id, left_type = self.generate_expr(expr.left)
    right_code, right_id, right_type = self.generate_expr(expr.right)
    result.extend(left_code)
    result.extend(right_code)

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
        '<=': 'OpULessThanEqual', '>=': 'OpUGreaterThanEqual', '&&': 'OpLogicalAnd', '||': 'OpLogicalOr',
        '&': 'OpBitwiseAnd', '|': 'OpBitwiseOr', '^': 'OpBitwiseXor',
        '<<': 'OpShiftLeftLogical', '>>': 'OpShiftRightLogical'
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
        result_type = self.type_ids['bool'] if expr.op in comparison_ops or expr.op in ['&&', '||'] else self.type_ids[
            'uint']

    result.append(f"{result_id} = {instr} {result_type} {left_id} {right_id}")
    return result, result_id, 'bool' if expr.op in comparison_ops else left_type


def _generate_cast(self, expr):
    result = []
    code, value_id, value_type = self.generate_expr(expr.expr)
    result.extend(code)

    target_type = expr.target_type
    target_type_id = self.type_ids[target_type]

    if value_type == target_type:
        return result, value_id, value_type

    result_id = self.new_id()

    # Determinar instrução de cast
    if value_type == 'uint' and target_type == 'float':
        op = 'OpConvertUToF'
    elif value_type == 'float' and target_type == 'uint':
        op = 'OpConvertFToU'
    elif value_type == 'float' and target_type == 'int':
        op = 'OpConvertFToU'  # Falso, mas necessário no Kernel mode
    elif value_type == 'int' and target_type == 'float':
        op = 'OpConvertUToF'  # Falso, mas necessário no Kernel mode
    elif value_type in ['int', 'uint'] and target_type in ['int', 'uint']:
        op = 'OpBitcast'
    else:
        raise Exception(f"Unsupported cast from {value_type} to {target_type}")

    result.append(f"{result_id} = {op} {target_type_id} {value_id}")
    return result, result_id, target_type