# lexer.py

def tokenize(source_code):
    tokens = []
    current = ''
    specials = {'(', ')', '{', '}', ':', ',', ';', '=', '+', '-', '*', '/', '%', '!', '<', '>', '&', '|'}
    multi_char_specials = {'->', '==', '!=', '<=', '>=' , '&&', '||'}
    i = 0

    while i < len(source_code):
        char = source_code[i]

        # Tenta pegar operadores de dois caracteres
        if i + 1 < len(source_code):
            two_chars = source_code[i] + source_code[i+1]
            if two_chars in multi_char_specials:
                if current:
                    tokens.append(current)
                    current = ''
                tokens.append(two_chars)
                i += 2
                continue

        # Se espaço ou quebra
        if char.isspace():
            if current:
                tokens.append(current)
                current = ''
            i += 1
        elif char in specials:
            if current:
                tokens.append(current)
                current = ''
            tokens.append(char)
            i += 1
        else:
            current += char
            i += 1

    if current:
        tokens.append(current)

    return tokens
