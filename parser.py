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

    def normalize_type(self, typ):
        if typ == "int":
            return "uint"
        return typ

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
        elif tok == "if":
            return self.parse_if()
        elif tok == "@cpu":
            return self.parse_cpu_block()
        else:
            return self.parse_assign()

    def parse_cpu_block(self):
        self.expect("@cpu")
        raw_code = self.next()  # O próximo token é TODO o código do bloco
        return sil_ast.CpuBlock(raw_code)

    def parse_if(self):
        self.expect("if")
        self.expect("(")
        condition = self.parse_expression()
        self.expect(")")
        self.expect("{")
        then_body = []
        while self.peek() != "}":
            then_body.append(self.parse_statement())
        self.expect("}")

        else_body = None
        if self.peek() == "else":
            self.expect("else")
            self.expect("{")
            else_body = []
            while self.peek() != "}":
                else_body.append(self.parse_statement())
            self.expect("}")

        return sil_ast.If(condition, then_body, else_body)

    def parse_var_decl(self):
        self.expect("var")
        name = self.next()
        self.expect(":")
        declared_type = self.normalize_type(self.next())
        self.expect("=")
        value = self.parse_expression()
        self.expect(";")

        # Auto-corrigir tipo se o valor for float
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

        # Auto-corrigir tipo se o valor for float
        if isinstance(value, sil_ast.Literal):
            if isinstance(value.value, float) and declared_type != "float":
                declared_type = "float"
            if isinstance(value.value, int) and declared_type not in ("int", "uint"):
                declared_type = "uint"

        return sil_ast.ConstDecl(name, declared_type, value)

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
        return sil_ast.Kernel(name, params, "void", body)

    def parse_params(self):
        params = []
        while self.peek() != ")":
            pname = self.next()
            self.expect(":")
            ptype = self.normalize_type(self.next())
            params.append(sil_ast.Param(pname, ptype))
            if self.peek() == ",":
                self.next()
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
            tok = self.peek()
            if tok in ('+', '-', '*', '/', '//', '==', '!=', '<', '>', '<=', '>=', '&&', '||'):
                op = self.next()
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
