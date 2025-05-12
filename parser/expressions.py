import sil_ast


# === Logical / Binary Expressions (precedence-aware) ===

def parse_logical_or(self):
    """
    Parses logical OR expressions (left-associative).
    Example: a || b || c
    """
    left = self.parse_logical_and()
    while self.peek() == '||':
        op = self.next()
        right = self.parse_logical_and()
        left = sil_ast.BinaryOp(left, op, right)
    return left


def parse_logical_and(self):
    """
    Parses logical AND expressions.
    Example: a && b && c
    """
    left = self.parse_equality()
    while self.peek() == '&&':
        op = self.next()
        right = self.parse_equality()
        left = sil_ast.BinaryOp(left, op, right)
    return left


def parse_equality(self):
    """
    Parses equality and inequality expressions.
    Example: a == b, a != b
    """
    left = self.parse_relational()
    while self.peek() in ['==', '!=']:
        op = self.next()
        right = self.parse_relational()
        left = sil_ast.BinaryOp(left, op, right)
    return left


def parse_relational(self):
    """
    Parses relational expressions.
    Example: a < b, a >= c
    """
    left = self.parse_additive()
    while self.peek() in ['<', '>', '<=', '>=']:
        op = self.next()
        right = self.parse_additive()
        left = sil_ast.BinaryOp(left, op, right)
    return left


def parse_additive(self):
    """
    Parses addition and subtraction.
    Example: a + b - c
    """
    left = self.parse_multiplicative()
    while self.peek() in ['+', '-']:
        op = self.next()
        right = self.parse_multiplicative()
        left = sil_ast.BinaryOp(left, op, right)
    return left


def parse_multiplicative(self):
    """
    Parses multiplication, division, floor-division and modulo.
    Example: a * b / c % d
    """
    left = self.parse_unary()
    while self.peek() in ['*', '/', '//', '%']:
        op = self.next()
        right = self.parse_unary()
        left = sil_ast.BinaryOp(left, op, right)
    return left


# === Unary & Primary Expressions ===

def parse_unary(self):
    """
    Parses unary operators and dereferencing/address-of.
    Supported: !, -, ~, *, &
    """
    tok = self.peek()
    if tok == '!':
        self.next()
        return sil_ast.UnaryOp('!', self.parse_unary())
    elif tok == '-':
        self.next()
        return sil_ast.UnaryOp('-', self.parse_unary())
    elif tok == '~':
        self.next()
        return sil_ast.UnaryOp('~', self.parse_unary())
    elif tok == '*':
        self.next()
        return sil_ast.Dereference(self.parse_unary())
    elif tok == '&':
        self.next()
        return sil_ast.AddressOf(self.parse_unary())
    else:
        return self.parse_primary()


def parse_primary(self):
    """
    Parses primary expressions:
    - literals
    - identifiers
    - grouped expressions in parentheses
    - cast and bitwise blocks
    """
    tok = self.peek()

    if tok == "bitwise":
        return self.parse_bitwise_block()
    if tok == "cast":
        return self.parse_cast_block()
    if tok == "(":
        self.next()
        expr = self.parse_expression()
        if self.peek() != ")":
            raise Exception(f"Expected ')', but found '{self.peek()}'")
        self.next()
        return expr

    tok = self.next()
    if tok is None:
        raise Exception("Unexpected end of input while parsing expression")

    # Numeric literals: decimal, float, hex
    if isinstance(tok, str):
        try:
            if tok.startswith(("0x", "0X")):
                return sil_ast.Literal(int(tok, 16))
            elif '.' in tok:
                return sil_ast.Literal(float(tok))
            elif tok.lstrip('-').isdigit():
                return sil_ast.Literal(int(tok))
        except ValueError:
            pass

    # Identifiers
    if self._is_identifier(tok):
        return sil_ast.Ident(tok)

    raise Exception(f"Unexpected token in expression: '{tok}'")


# === Bitwise Block Expressions ===

def parse_bitwise_block(self):
    """
    Parses a 'bitwise { ... }' block.
    This block evaluates only bitwise logic (&, |, ^, <<, >>)
    """
    self.expect("bitwise")
    self.expect("{")
    expr = self.parse_bitwise_expression()
    self.expect("}")
    return sil_ast.BitwiseExpr(expr)


def parse_bitwise_expression(self):
    """
    Parses a chain of bitwise binary operations.
    """
    left = self.parse_bitwise_unary()
    while self.peek() in ['&', '|', '^', '<<', '>>']:
        op = self.next()
        right = self.parse_bitwise_unary()
        left = sil_ast.BinaryOp(left, op, right)
    return left


def parse_bitwise_unary(self):
    """
    Parses unary ops within a bitwise expression.
    Supported: ~, -
    """
    tok = self.peek()
    if tok in ['~', '-']:
        self.next()
        operand = self.parse_bitwise_unary()
        return sil_ast.UnaryOp(tok, operand)
    else:
        return self.parse_bitwise_primary()


def parse_bitwise_primary(self):
    """
    Parses literals and identifiers inside a bitwise block.
    Supports parentheses to group expressions.
    """
    tok = self.peek()

    if tok == "(":
        self.next()
        expr = self.parse_bitwise_expression()
        if self.peek() != ")":
            raise Exception(f"Expected ')', but found '{self.peek()}'")
        self.next()
        return expr

    tok = self.next()
    if tok is None:
        raise Exception("Unexpected end of input in bitwise expression")

    if isinstance(tok, str) and tok.isdigit():
        return sil_ast.Literal(int(tok))

    try:
        if '.' in tok:
            return sil_ast.Literal(float(tok))
        if tok.lstrip('-').isdigit():
            return sil_ast.Literal(int(tok))
    except ValueError:
        pass

    if self._is_identifier(tok):
        return sil_ast.Ident(tok)

    raise Exception(f"Unexpected token in bitwise expression: '{tok}'")


# === Cast Block ===

def parse_cast_block(self):
    """
    Parses a cast block of the form:
        cast { expression as target_type }
    """
    self.expect("cast")
    self.expect("{")
    expr = self.parse_expression()
    self.expect("as")
    target_type = self.next()
    self.expect("}")
    return sil_ast.CastExpr(expr, target_type)
