import sil_ast


def parse_if(self):
    self.expect("if")
    self.expect("(")
    condition = self.parse_expression()
    self.expect(")")
    self.expect("{")
    then_body = []
    while self.peek() != "}":
        if self.peek() is None:
            raise Exception("Fim inesperado do arquivo ao analisar bloco 'if'")
        then_body.append(self.parse_statement())
    self.expect("}")

    else_body = None
    if self.peek() == "else":
        self.expect("else")
        self.expect("{")
        else_body = []
        while self.peek() != "}":
            if self.peek() is None:
                raise Exception("Fim inesperado do arquivo ao analisar bloco 'else'")
            else_body.append(self.parse_statement())
        self.expect("}")

    return sil_ast.If(condition, then_body, else_body)

def parse_loop(self):
    self.expect("loop")
    self.expect("{")
    body = []
    while self.peek() != "}":
        if self.peek() is None:
            raise Exception("Fim inesperado no corpo do loop")
        body.append(self.parse_statement())
    self.expect("}")
    return sil_ast.Loop(body)

