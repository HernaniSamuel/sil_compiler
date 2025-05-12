import sil_ast


def parse_kernel(self):
    """
    Parses a kernel definition of the form:
        kernel name(param1: type1, param2: type2, ...) {
            // statements
        }

    Returns:
        sil_ast.Kernel: an AST node representing the kernel.
    """
    self.expect("kernel")
    name = self.next()

    if not self._is_identifier(name):
        raise Exception(f"Invalid kernel name: '{name}'")

    self.expect("(")
    params = self.parse_params()
    self.expect(")")
    self.expect("{")

    body = []

    # Optional debug: print the tokens inside the kernel body
    if self.debug:
        print(f"Kernel '{name}' - tokens in body:")
        debug_pos = self.pos
        debug_tokens = []
        open_braces = 1  # We're already inside the opening '{'

        # Collect all tokens inside the kernel block (without the final '}')
        while debug_pos < len(self.tokens) and open_braces > 0:
            if self.tokens[debug_pos] == '{':
                open_braces += 1
            elif self.tokens[debug_pos] == '}':
                open_braces -= 1
            if open_braces > 0:
                debug_tokens.append(self.tokens[debug_pos])
            debug_pos += 1

        print(debug_tokens)

    # Parse kernel body statements until closing '}'
    while self.peek() != "}":
        if self.peek() is None:
            raise Exception(
                f"Unexpected end of file while parsing body of kernel '{name}'"
            )

        try:
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        except Exception as e:
            print(f"Error parsing statement in kernel '{name}': {str(e)}")
            self.error_recovery()

            # Stop early if recovery hit the closing brace
            if self.peek() == "}":
                break
            raise

    self.expect("}")
    return sil_ast.Kernel(name, params, "void", body)


def parse_params(self):
    """
    Parses the parameter list inside a kernel's parentheses:
        (name1: type1, name2: type2, ...)

    Returns:
        list[sil_ast.Param]: list of parameter AST nodes.
    """
    params = []

    while self.peek() != ")":
        pname = self.next()
        if not self._is_identifier(pname):
            raise Exception(f"Invalid parameter name: '{pname}'")

        self.expect(":")
        ptype = self.normalize_type(self.next())
        params.append(sil_ast.Param(pname, ptype))

        if self.peek() == ",":
            self.next()
        elif self.peek() != ")":
            raise Exception(
                f"Expected ',' or ')' after parameter, but found '{self.peek()}'"
            )

    return params
