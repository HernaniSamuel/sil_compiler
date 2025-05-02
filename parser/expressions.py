import sil_ast


def parse_logical_or(self):
    left = self.parse_logical_and()
    while self.peek() == '||':
        op = self.next()
        right = self.parse_logical_and()
        left = sil_ast.BinaryOp(left, op, right)
    return left

def parse_logical_and(self):
    left = self.parse_equality()
    while self.peek() == '&&':
        op = self.next()
        right = self.parse_equality()
        left = sil_ast.BinaryOp(left, op, right)
    return left

def parse_equality(self):
    left = self.parse_relational()
    while self.peek() in ['==', '!=']:
        op = self.next()
        right = self.parse_relational()
        left = sil_ast.BinaryOp(left, op, right)
    return left

def parse_relational(self):
    left = self.parse_additive()
    while self.peek() in ['<', '>', '<=', '>=']:
        op = self.next()
        right = self.parse_additive()
        left = sil_ast.BinaryOp(left, op, right)
    return left

def parse_unary(self):
    tok = self.peek()
    if tok == '!':
        self.next()
        operand = self.parse_unary()
        return sil_ast.UnaryOp('!', operand)
    elif tok == '-':
        self.next()
        operand = self.parse_unary()
        return sil_ast.UnaryOp('-', operand)
    else:
        return self.parse_primary()

def parse_additive(self):
    left = self.parse_multiplicative()
    while self.peek() in ['+', '-']:
        op = self.next()
        right = self.parse_multiplicative()
        left = sil_ast.BinaryOp(left, op, right)
    return left

def parse_multiplicative(self):
    left = self.parse_unary()
    while self.peek() in ['*', '/', '//', '%']:
        op = self.next()
        right = self.parse_unary()
        left = sil_ast.BinaryOp(left, op, right)
    return left

def parse_primary(self):
    tok = self.peek()

    # Detectar parênteses para subexpressões
    if tok == "(":
        self.next()  # Consumir o parêntese de abertura
        expr = self.parse_expression()
        if self.peek() != ")":
            raise Exception(f"Esperado ')', mas encontrado '{self.peek()}'")
        self.next()  # Consumir o parêntese de fechamento
        return expr

    # Caso contrário, proceder com a análise normal
    tok = self.next()

    if tok is None:
        raise Exception("Fim inesperado da entrada durante a análise da expressão")

    # Verificar literais numéricos
    if isinstance(tok, str) and tok.isdigit():
        return sil_ast.Literal(int(tok))

    try:
        # Verificar se é um float
        if isinstance(tok, str) and '.' in tok:
            return sil_ast.Literal(float(tok))
        # Verificar se é um int
        if isinstance(tok, str) and tok.lstrip('-').isdigit():
            return sil_ast.Literal(int(tok))
    except ValueError:
        pass

    # Se não é um literal numérico, deve ser um identificador
    if self._is_identifier(tok):
        return sil_ast.Ident(tok)
    else:
        raise Exception(f"Token inesperado na expressão: '{tok}'")
