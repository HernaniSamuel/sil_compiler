import lexer
import parser
import generator

source_code = """
kernel main(a: int, b: int, out: int) {
    var id: int = 0;
    var va: int = a;
    var vb: int = b;
    var sum: int = va + vb;
    out = sum;
    return;
}
"""

tokens = lexer.tokenize(source_code)
p = parser.Parser(tokens)
ast_tree = p.parse()

g = generator.Generator()
assembly = g.generate(ast_tree)

# Salvar o assembly SPIR-V textual
with open("output.spvasm", "w") as f:
    f.write(assembly)

print("✅ Assembly SPIR-V gerado em output.spvasm")
