import sil_ast


def parse_var_decl(self):
    """
    Parses a variable declaration of the form:
        var name: type = expression;
    Infers the correct type if the value is a literal.
    """
    self.expect("var")
    name = self.next()
    if not self._is_identifier(name):
        raise Exception(f"Invalid variable name: '{name}'")

    self.expect(":")
    declared_type = self.normalize_type(self.next())
    self.expect("=")
    value = self.parse_expression()

    if self.debug:
        print(f"Before expect(';'), pos={self.pos}, next token={self.peek()}")

    self.expect(";")

    # Automatically adjust type for literal values
    if isinstance(value, sil_ast.Literal):
        if isinstance(value.value, float) and declared_type != "float":
            declared_type = "float"
        if isinstance(value.value, int) and declared_type not in ("int", "uint"):
            declared_type = "uint"

    return sil_ast.VarDecl(name, declared_type, value)


def parse_const_decl(self):
    """
    Parses a constant declaration of the form:
        const name: type = expression;
    """
    self.expect("const")
    name = self.next()
    self.expect(":")
    declared_type = self.normalize_type(self.next())
    self.expect("=")
    value = self.parse_expression()
    self.expect(";")

    # Automatically adjust type for literal values
    if isinstance(value, sil_ast.Literal):
        if isinstance(value.value, float) and declared_type != "float":
            declared_type = "float"
        if isinstance(value.value, int) and declared_type not in ("int", "uint"):
            declared_type = "uint"

    return sil_ast.ConstDecl(name, declared_type, value)


def parse_assign(self):
    """
    Parses a simple assignment:
        x = expression;
    """
    name = self.next()
    if name is None:
        raise Exception("Expected identifier at start of assignment")
    if self.peek() != "=":
        raise Exception(f"Expected '=' after '{name}', found '{self.peek()}'")
    self.expect("=")
    value = self.parse_expression()
    self.expect(";")
    return sil_ast.Assign(name, value)


def parse_return(self):
    """
    Parses a return statement:
        return [expression];
    """
    self.expect("return")
    value = None
    if self.peek() != ";":
        value = self.parse_expression()
    self.expect(";")
    return sil_ast.Return(value)


def parse_statement(self):
    """
    Parses any valid statement: variable/const declarations, return, if, loop,
    break, or assignment. Handles expressions and @cpu blocks.
    """
    tok = self.peek()

    if self.debug:
        print(f"Parsing statement, token: {tok}")

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
        # Handle potential assignment (identifier or pointer deref)
        if self.peek() == "*" or self._is_identifier(self.peek()):
            start_pos = self.pos
            try:
                lhs = self.parse_expression()
                if self.peek() == "=":
                    self.expect("=")
                    rhs = self.parse_expression()
                    self.expect(";")
                    return sil_ast.Assign(lhs, rhs)
                else:
                    # Roll back if not a valid assignment
                    self.pos = start_pos
            except Exception:
                self.pos = start_pos

        raise Exception(f"Unexpected token: '{tok}' at position {self.pos}")


def is_identifier(self, token):
    """
    Checks if a token is a valid identifier:
    starts with a letter or underscore, and contains only alphanumerics or underscores.
    """
    if token is None or not isinstance(token, str):
        return False
    if not token:
        return False
    if not (token[0].isalpha() or token[0] == "_"):
        return False
    return all(c.isalnum() or c == "_" for c in token)
