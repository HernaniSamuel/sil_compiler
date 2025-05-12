import sil_ast


def parse_if(self):
    """
    Parses an if-statement with optional else block.

    Syntax:
        if (condition) {
            // then_body
        }
        else {
            // else_body (optional)
        }

    Returns:
        sil_ast.If: an AST node representing the conditional.
    """
    self.expect("if")
    self.expect("(")
    condition = self.parse_expression()
    self.expect(")")
    self.expect("{")

    then_body = []
    while self.peek() != "}":
        if self.peek() is None:
            raise Exception("Unexpected end of file while parsing 'if' block")
        then_body.append(self.parse_statement())
    self.expect("}")

    else_body = None
    if self.peek() == "else":
        self.expect("else")
        self.expect("{")
        else_body = []
        while self.peek() != "}":
            if self.peek() is None:
                raise Exception("Unexpected end of file while parsing 'else' block")
            else_body.append(self.parse_statement())
        self.expect("}")

    return sil_ast.If(condition, then_body, else_body)


def parse_loop(self):
    """
    Parses an infinite loop construct.

    Syntax:
        loop {
            // body
        }

    Returns:
        sil_ast.Loop: an AST node representing the loop.
    """
    self.expect("loop")
    self.expect("{")

    body = []
    while self.peek() != "}":
        if self.peek() is None:
            raise Exception("Unexpected end of file inside loop body")
        body.append(self.parse_statement())
    self.expect("}")

    return sil_ast.Loop(body)
