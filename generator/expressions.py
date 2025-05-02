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
    else:
        raise Exception(f"Unsupported expression type: {type(expr)}")

def _generate_literal(self, expr):
    result = []
    const_id = self.get_constant(expr.value)
    if isinstance(expr.value, int):
        return result, const_id, 'uint'
    elif isinstance(expr.value, float):
        return result, const_id, 'float'
    else:
        raise Exception(f"Unsupported literal type: {type(expr.value)}")

def _generate_ident(self, expr):
    result = []
    if expr.name in self.var_ids:
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
        result_type = self.type_ids['bool'] if expr.op in comparison_ops or expr.op in ['&&', '||'] else self.type_ids['uint']

    result.append(f"{result_id} = {instr} {result_type} {left_id} {right_id}")
    return result, result_id, 'bool' if expr.op in comparison_ops else left_type
