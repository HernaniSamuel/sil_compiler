# sil_ast.py

class VarDecl:
    def __init__(self, name, var_type, value):
        self.name = name
        self.var_type = var_type
        self.value = value

    def __repr__(self):
        return f"VarDecl(name={self.name}, type={self.var_type}, value={self.value})"

class ConstDecl:
    def __init__(self, name, const_type, value):
        self.name = name
        self.const_type = const_type
        self.value = value

    def __repr__(self):
        return f"ConstDecl(name={self.name}, type={self.const_type}, value={self.value})"

class Param:
    def __init__(self, name, param_type):
        self.name = name
        self.param_type = param_type

    def __repr__(self):
        return f"Param(name={self.name}, type={self.param_type})"

class Kernel:
    def __init__(self, name, params, return_type, body):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body

    def __repr__(self):
        return f"Kernel(name={self.name}, params={self.params}, return_type={self.return_type}, body={self.body})"

class Return:
    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        return f"Return(value={self.value})"

class Assign:
    def __init__(self, target, value):
        self.target = target  # Ident ou Dereference
        self.value = value
    def __repr__(self):
        return f"Assign(target={self.target}, value={self.value})"

class If:
    def __init__(self, condition, then_body, else_body=None):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body

    def __repr__(self):
        return f"If(condition={self.condition}, then_body={self.then_body}, else_body={self.else_body})"

class Loop:
    def __init__(self, body):
        self.body = body

    def __repr__(self):
        return f"Loop(body={self.body})"

class Break:
    def __repr__(self):
        return "Break()"

class Continue:
    def __repr__(self):
        return "Continue()"

class BinaryOp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"BinaryOp(left={self.left}, op='{self.op}', right={self.right})"

class UnaryOp:
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def __repr__(self):
        return f"UnaryOp(op='{self.op}', expr={self.expr})"

class Literal:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Literal(value={self.value})"

class Ident:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Ident(name={self.name})"

class CpuBlock:
    def __init__(self, code):
        self.code = code

    def __repr__(self):
        return f"CpuBlock(code={self.code})"

class BitwiseExpr:
    def __init__(self, expr):
        self.expr = expr  # Pode ser uma árvore de operações bitwise

class CastExpr:
    def __init__(self, expr, target_type):
        self.expr = expr
        self.target_type = target_type

class Dereference:
    def __init__(self, expr):
        self.expr = expr
    def __repr__(self):
        return f"Dereference({self.expr})"

class AddressOf:
    def __init__(self, expr):
        self.expr = expr
    def __repr__(self):
        return f"AddressOf({self.expr})"
