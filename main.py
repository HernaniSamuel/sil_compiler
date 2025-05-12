import sys
import os
import subprocess
import traceback
import lexer
from parser import parser
from generator import generator
import sil_ast
from runtime.host import HostRuntime
from minisil import transform


def display_tokens(tokens, max_per_line=10):
    """
    Pretty-prints a list of tokens, grouped by line length.

    Args:
        tokens (list): List of tokens to display.
        max_per_line (int): Number of tokens per printed line.
    """
    print("\nGENERATED TOKENS:")
    for i in range(0, len(tokens), max_per_line):
        chunk = tokens[i:i + max_per_line]
        line = " ".join([f"'{t}'" if isinstance(t, str) else str(t) for t in chunk])
        print(f"{i:4d}: {line}")
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py path/to/file.sil [--debug]")
        sys.exit(1)

    filename = sys.argv[1]
    debug_mode = "--debug" in sys.argv

    basename = os.path.splitext(os.path.basename(filename))[0]
    folder = os.path.dirname(filename) or "."

    try:
        # Load source code
        with open(filename, "r", encoding="utf-8") as f:
            original_code = f.read()

        print(f"Compiling {filename}...")
        print("Preprocessing with Mini-SIL...")

        # Transform code (handle array unrolling, loop rewriting, etc.)
        source_code = transform(original_code)

        print(f"Compiling {filename}...")

        # Tokenize source
        tokens = lexer.tokenize(source_code)

        # Show tokens
        if debug_mode:
            display_tokens(tokens)
        else:
            print("First 20 tokens:", tokens[:20])

        # Warnings for specific patterns
        if '//' in tokens:
            locations = [i for i, t in enumerate(tokens) if t == '//']
            print(f"WARNING: Token '//' found at positions: {locations}")
        if ';' not in tokens:
            print("ALERT: No semicolon ';' tokens found!")

        # Parse AST
        p = parser.Parser(tokens)
        ast_tree = p.parse()

        # Optionally show AST structure
        if debug_mode:
            print("\nAST STRUCTURE:")
            for i, node in enumerate(ast_tree):
                print(f"Node {i}: {type(node).__name__}")
                if isinstance(node, sil_ast.Kernel):
                    print(f"  Kernel: {node.name}")
                    print(f"  Params: {len(node.params)}")
                    print(f"  Body statements: {len(node.body)}")
                elif isinstance(node, sil_ast.CpuBlock):
                    preview = node.code[:50].replace("\n", " ")
                    print(f"  CpuBlock: {preview}...")

        # Separate CPU and GPU nodes
        g = generator.Generator()
        gpu_nodes = [n for n in ast_tree if not isinstance(n, sil_ast.CpuBlock)]
        cpu_nodes = [n for n in ast_tree if isinstance(n, sil_ast.CpuBlock)]

        # Compile GPU code to SPIR-V
        spv_filename = None
        if gpu_nodes:
            print("Generating SPIR-V assembly...")
            assembly = g.generate(gpu_nodes)

            spvasm_filename = os.path.join(folder, f"{basename}.spvasm")
            spv_filename = os.path.join(folder, f"{basename}.spv")

            # Save .spvasm file
            with open(spvasm_filename, "w") as f:
                f.write(assembly)

            # Assemble to .spv binary
            print(f"Assembling SPIR-V to {spv_filename}...")
            result = subprocess.run(
                ["spirv-as", spvasm_filename, "-o", spv_filename],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print("SPIR-V assembly failed:")
                print(result.stderr)
                sys.exit(1)

            print("SPIR-V assembly succeeded.")

        # Validate the .spv file
        if spv_filename:
            print(f"Validating {spv_filename}...")
            result = subprocess.run(
                ["spirv-val", spv_filename],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print("SPIR-V validation failed:")
                print(result.stderr)
                sys.exit(1)

            print("SPIR-V validation passed.")

        # Execute CPU-side code if present
        if cpu_nodes and spv_filename:
            print("Running CPU block(s)...")
            rt = HostRuntime()
            rt.load_spirv(spv_filename)

            # Expose runtime to CPU code blocks
            globals()["rt"] = rt
            globals()["gpu"] = rt  # alias

            for node in cpu_nodes:
                exec(node.code, globals())

            print("CPU block execution completed.")

    except Exception as e:
        print(f"Error during compilation: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
