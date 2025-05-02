import sil_ast

def parse_var_decl(self):
    self.expect("var")
    name = self.next()
    if not self._is_identifier(name):
        raise Exception(f"Nome de variável inválido: '{name}'")

    self.expect(":")
    declared_type = self.normalize_type(self.next())
    self.expect("=")
    value = self.parse_expression()

    # Debug: posição atual antes de expect(";")
    if self.debug:
        print(f"Antes de expect(';'), posição={self.pos}, próximo token={self.peek()}")

    self.expect(";")

    # Auto-corrigir tipo se o valor for float/int
    if isinstance(value, sil_ast.Literal):
        if isinstance(value.value, float) and declared_type != "float":
            declared_type = "float"
        if isinstance(value.value, int) and declared_type not in ("int", "uint"):
            declared_type = "uint"

    return sil_ast.VarDecl(name, declared_type, value)

def parse_const_decl(self):
    self.expect("const")
    name = self.next()
    self.expect(":")
    declared_type = self.normalize_type(self.next())
    self.expect("=")
    value = self.parse_expression()
    self.expect(";")

    # Auto-corrigir tipo se o valor for float/int
    if isinstance(value, sil_ast.Literal):
        if isinstance(value.value, float) and declared_type != "float":
            declared_type = "float"
        if isinstance(value.value, int) and declared_type not in ("int", "uint"):
            declared_type = "uint"

    return sil_ast.ConstDecl(name, declared_type, value)

def parse_assign(self):
    name = self.next()
    if name is None:
        raise Exception("Esperado identificador no início da atribuição")
    if self.peek() != "=":
        raise Exception(f"Esperado '=' depois de '{name}', mas encontrado '{self.peek()}'")
    self.expect("=")
    value = self.parse_expression()
    self.expect(";")
    return sil_ast.Assign(name, value)

def parse_return(self):
    self.expect("return")
    value = None
    if self.peek() != ";":
        value = self.parse_expression()
    self.expect(";")
    return sil_ast.Return(value)

def parse_statement(self):
    tok = self.peek()

    if self.debug:
        print(f"Analisando declaração, token: {tok}")

    if tok == "var":
        return self.parse_var_decl()
    elif tok == "const":
        return self.parse_const_decl()
    elif tok == "kernel":
        return self.parse_kernel()
    elif tok == "return":
        return self.parse_return()
    elif tok == "if":
        return self.parse_if()
    elif tok == "loop":
        return self.parse_loop()
    elif tok == "break":
        self.next()
        self.expect(";")
        return sil_ast.Break()

    elif tok == "@cpu":
        return self.parse_cpu_block()
    else:
        # Verifica se é um identificador de variável antes de tentar parse_assign
        if self._is_identifier(tok) and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1] == "=":
            return self.parse_assign()
        else:
            raise Exception(f"Token inesperado: '{tok}' na posição {self.pos}")

def is_identifier(self, token):
    if token is None:
        return False
    if not isinstance(token, str):
        return False
    # Um identificador válido começa com letra ou _ e pode conter letras, números e _
    if not token:
        return False
    if not (token[0].isalpha() or token[0] == '_'):
        return False
    for char in token:
        if not (char.isalnum() or char == '_'):
            return False
    return True
