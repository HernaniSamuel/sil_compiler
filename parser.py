# parser.py

import sil_ast

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def next(self):
        tok = self.peek()
        if tok is not None:
            self.pos += 1
        return tok

    def expect(self, expected):
        tok = self.next()
        if tok != expected:
            raise Exception(f"Esperado '{expected}', mas encontrado '{tok}'")

    def parse(self):
        statements = []
        while self.peek() is not None:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return statements

    def parse_statement(self):
        tok = self.peek()

        if tok == "var":
            return self.parse_var_decl()
        elif tok == "const":
            return self.parse_const_decl()
        elif tok == "kernel":
            return self.parse_kernel()
        elif tok == "return":
            return self.parse_return()
        else:
            # Nova regra: parse de atribuição (assignment)
            return self.parse_assign()

    def parse_var_decl(self):
        self.expect("var")
        name = self.next()
        self.expect(":")
        var_type = self.next()
        self.expect("=")
        value = self.parse_expression()
        self.expect(";")
        return sil_ast.VarDecl(name, var_type, value)

    def parse_const_decl(self):
        self.expect("const")
        name = self.next()
        self.expect(":")
        const_type = self.next()
        self.expect("=")
        value = self.parse_expression()
        self.expect(";")
        return sil_ast.ConstDecl(name, const_type, value)

    def parse_kernel(self):
        self.expect("kernel")
        name = self.next()
        self.expect("(")
        params = self.parse_params()
        self.expect(")")
        self.expect("{")
        body = []
        while self.peek() != "}":
            body.append(self.parse_statement())
        self.expect("}")
        return sil_ast.Kernel(name, params, "void", body)  # Kernel é sempre void, automático

    def parse_params(self):
        params = []
        while self.peek() != ")":
            pname = self.next()
            self.expect(":")
            ptype = self.next()
            params.append(sil_ast.Param(pname, ptype))
            if self.peek() == ",":
                self.next()  # consumir a vírgula
        return params

    def parse_return(self):
        self.expect("return")
        value = None
        if self.peek() != ";":
            value = self.parse_expression()
        self.expect(";")
        return sil_ast.Return(value)

    def parse_expression(self):
        left = self.parse_primary()

        while True:
            op = self.peek()
            if op in ('+', '-', '*', '/'):
                self.next()  # consome o operador
                right = self.parse_primary()
                left = sil_ast.BinaryOp(left, op, right)
            else:
                break

        return left

    def parse_primary(self):
        tok = self.next()

        if tok.isdigit():
            return sil_ast.Literal(int(tok))
        try:
            float(tok)
            return sil_ast.Literal(float(tok))
        except ValueError:
            pass

        return sil_ast.Ident(tok)

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
