def tokenize(source_code):
    """
    Lexical analyzer for Mini-SIL source code.

    Splits the input source into tokens, including:
    - identifiers
    - literals
    - symbols/operators
    - keywords like @cpu

    Supports:
    - block comments (/* ... */)
    - multi-character operators (==, !=, <=, >=, //, >>, etc.)
    - float numbers with dots
    - raw blocks after @cpu

    Args:
        source_code (str): The SIL source code as a string.

    Returns:
        list: A flat list of tokens as strings.
    """
    tokens = []
    current = ''

    # Single-character special tokens
    specials = {
        '(', ')', '{', '}', ':', ',', ';', '=', '+', '-', '*',
        '/', '%', '!', '<', '>', '&', '|', '~', '.'
    }

    # Multi-character operators
    multi_char_specials = {
        '->', '==', '!=', '<=', '>=', '&&', '||', '//', '>>', '<<'
    }

    i = 0
    while i < len(source_code):
        # Handle block comments: /* ... */
        if (
            i + 1 < len(source_code)
            and source_code[i] == '/'
            and source_code[i + 1] == '*'
        ):
            i += 2
            while (
                i + 1 < len(source_code)
                and not (source_code[i] == '*' and source_code[i + 1] == '/')
            ):
                i += 1
            i += 2 if i + 1 < len(source_code) else 1
            continue

        # Handle two-character operators (e.g., //, ==)
        if i + 1 < len(source_code):
            two_chars = source_code[i] + source_code[i + 1]
            if two_chars in multi_char_specials:
                if current:
                    tokens.append(current)
                    current = ''
                tokens.append(two_chars)
                i += 2
                continue

        char = source_code[i]

        if char.isspace():
            # End of identifier/literal
            if current:
                tokens.append(current)
                current = ''
            i += 1

        elif char == '@':
            # Handle @cpu and similar directives
            if current:
                tokens.append(current)
                current = ''
            word = '@'
            i += 1
            while i < len(source_code) and (
                source_code[i].isalnum() or source_code[i] == '_'
            ):
                word += source_code[i]
                i += 1
            tokens.append(word)

            # Handle @cpu block specially: capture raw trailing code
            if word == "@cpu":
                raw_code = ""

                # Skip any whitespace after @cpu
                while i < len(source_code) and source_code[i].isspace():
                    i += 1

                # Capture all remaining code as raw CPU block
                while i < len(source_code):
                    raw_code += source_code[i]
                    i += 1
                tokens.append(raw_code)
                break  # @cpu always ends the SIL code
            continue

        elif char in specials:
            # Check for float pattern like "2 . 5" (space-separated float)
            if (
                char == '.'
                and current.isdigit()
                and i + 1 < len(source_code)
                and source_code[i + 1].isdigit()
            ):
                current += char
                i += 1
                continue

            if current:
                tokens.append(current)
                current = ''
            tokens.append(char)
            i += 1

        else:
            # Accumulate identifier, number, etc.
            current += char
            i += 1

    # Flush last accumulated token
    if current:
        tokens.append(current)

    return tokens
