# 🧠 SIL (SIL Intermediate Language)

**SIL** is a minimalist, typed intermediate language designed to be compiled into [SPIR-V](https://www.khronos.org/spir/), the low-level intermediate representation used in GPU programming.

This project includes a full compiler pipeline:
- Lexical analysis
- Parsing into an AST
- Optional preprocessing (`MiniSIL`)
- SPIR-V code generation
- Runtime execution on the GPU via `pyopencl`

> **Note:** `minisil.py` is an optional preprocessor that expands high-level array constructs into scalar operations.

---

## ✨ Features

- ✔️ Typed variables: `uint`, `float`, `bool`, pointers
- ✔️ Kernel definitions with parameters
- ✔️ Arithmetic, logical, bitwise, and cast expressions
- ✔️ Control flow: `if`, `loop`, `break`, `return`
- ✔️ `@cpu` blocks for CPU-side assertions and I/O
- ✔️ Array unrolling support via MiniSIL
- ✔️ SPIR-V validation and execution using `pyopencl`

---

## 📚 SIL Language Overview

```sil
kernel sum(out: uint) {
    var a: uint = 12;
    var b: uint = 18;
    out = a + b;
}

@cpu
import numpy as np, pyopencl as cl
buf = np.zeros(1, dtype=np.uint32)
out = rt.create_buffer(buf, cl.mem_flags.READ_WRITE)
rt.run_kernel("sum", 1, {"out": out})
result = rt.read_buffer(out, np.uint32, (1,))[0]
print("Result:", result)
assert result == 30, "Fail: incorrect result"
```

- `kernel`: Defines a GPU kernel.
- `var`: Declares a local variable.
- `@cpu`: Embeds a Python code block that runs after the GPU finishes.

---

## ⚙️ Project Structure

```
sil/
├── generator/       # SPIR-V code generation logic
├── parser/          # Parser (SIL → AST)
├── runtime/         # pyopencl runtime interface
├── sil_tests/       # Test suite in .sil files
├── sil_ast.py       # AST node definitions
├── minisil.py       # Preprocessor for arrays
├── test_runner.py   # Runs and validates SIL tests
├── lexer.py         # Simple handwritten lexer for SIL
└── main.py          # Compiler entry point
```

---

## 🚀 Getting Started

### 1. Set up environment

```bash
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Run a SIL file

```bash
python main.py sil_tests/basic_ops/basic_ops.sil
```

### 3. Run all tests

```bash
python test_runner.py
```

---

## 🧪 Example Test File

```sil
kernel bitwise_extreme(out: uint = array[2]) {
    var val: uint = 1;
    out[0] = bitwise{ val << 31 };
    out[1] = bitwise{ (val << 31) >> 31 };
}

@cpu
def bitwise_extreme(**inputs):
    val = 1
    shifted = (val << 31) & 0xFFFFFFFF
    recovered = (shifted >> 31) & 0xFFFFFFFF

    actual0 = inputs["OUT_0"][0]
    actual1 = inputs["OUT_1"][0]

    print(f"OUT_0 = {actual0}, esperado = {shifted}")
    print(f"OUT_1 = {actual1}, esperado = {recovered}")

    if actual0 != shifted or actual1 != recovered:
        raise Exception("Teste bitwise_extreme falhou")
```

---

## 📌 Limitations

- ❌ No native support for dynamic-length arrays
- ❌ No structs, functions, or recursion
- ❌ Limited type inference and no type polymorphism
- 🔧 Array support is emulated via the `MiniSIL` preprocessor
- 🚫 No full GPU thread model: 
  - No `get_global_id`, `get_local_id`, or `workgroup` support
  - No atomics or barriers
  - Parallelism is limited due to lack of indexable memory

> ⚠️ The lack of true arrays made it extremely difficult to implement GPU features like `get_global_id()`, which limits the parallelism model.

---

## 🧰 Requirements

To compile and run SIL programs, make sure the following tools are installed:

- **[Vulkan SDK](https://vulkan.lunarg.com/sdk/home)**  
  Includes `spirv-as` and `spirv-val`, which are required to assemble and validate SPIR-V binaries.
  > After installing, make sure the SDK's `bin/` directory is added to your system `PATH`.

- **[PyOpenCL](https://github.com/inducer/pyopencl)**  
  Used as a runtime to load and launch SPIR-V kernels on the GPU.

You can verify installation with:

```bash
spirv-as --version
spirv-val --version
```

---
## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.

© 2025 Hernani Samuel Diniz
