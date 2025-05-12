# -*- coding: utf-8 -*-
"""
Mini‑SIL: A temporary array + loop expander for the SIL compiler
=================================================================

Mini‑SIL is a transformation layer that expands arrays and unrolls loops
in SIL source code into flat scalar variables and operations, allowing
the SIL compiler to process array-based computations without native array support.

🧠 Why Mini‑SIL exists:
This is the only viable solution I found to enable array usage in SIL
while I continue learning how to implement true array support (e.g., OpTypeArray)
in the compiler's backend.

Mini‑SIL lets me develop and test new language features quickly, and prove the
language's capabilities with real AI workloads — like fast style transfer and
semantic segmentation — before low-level array support is complete.

🔁 How it works:
- Any for loop is expanded into repeated lines of scalar operations.
- Arrays like a[2][3] are flattened into a_0_0, a_0_1, ..., a_1_2.
- Only for loops are allowed to iterate over arrays.
- You must not place a for inside a loop{} block — this will break.

🧪 Use for only when necessary — it duplicates code, not logic.
Other loops (loop{}) remain untouched and should be used for control flow.

🔒 Future:
The for construct will stay in the language as a distinct loop type,
so your existing SIL code will remain valid and portable even after
native arrays are supported.

🤝 Want to help?
If you have a working solution for real array support in SPIR-V (e.g., with
OpTypeArray and OpAccessChain), feel free to fork and implement it —
your contributions are more than welcome!
"""

from __future__ import annotations

import itertools
import re
from typing import List, Tuple

# ---------------------------------------------------------------------------
# 1) Arrays → escalares
# ---------------------------------------------------------------------------

_ArrayMapping = List[Tuple[str, Tuple[int, ...], str]]  # (base, indices, nome)

ARRAY_DECL_RE = re.compile(r"var\s+(\w+)\s*:\s*(\w+)\s*=\s*array((?:\[\d+])+);?")
KERNEL_RE = re.compile(r"kernel\s+(\w+)\s*\(([^)]*)\)\s*\{")


def _expand_dimensions(dim_spec: str) -> List[int]:
    """"[2][4]" → [2, 4]"""
    return list(map(int, re.findall(r"\[(\d+)\]", dim_spec)))


def _expand_combinations(sizes: List[int]):
    return itertools.product(*[range(s) for s in sizes])


# ---------------------------------------------------------------------------
# 2) Expansão de declarações de arrays (variáveis locais)
# ---------------------------------------------------------------------------

def expand_array_declaration(line: str) -> tuple[str | None, _ArrayMapping]:
    """Converte `var a: uint = array[2][3];` em 6 declarações escalares."""
    m = ARRAY_DECL_RE.match(line.strip())
    if not m:
        return None, []

    name, typ, dims_str = m.group(1), m.group(2), m.group(3)
    sizes = _expand_dimensions(dims_str)
    decls, mapping = [], []
    for idxs in _expand_combinations(sizes):
        sc_name = f"{name}_{'_'.join(map(str, idxs))}"
        decls.append(f"var {sc_name}: {typ} = 0;")
        mapping.append((name, idxs, sc_name))
    return "\n".join(decls), mapping


# ---------------------------------------------------------------------------
# 3) Expansão de parâmetros array no cabeçalho do kernel
# ---------------------------------------------------------------------------

def expand_kernel_parameters(code: str) -> tuple[str, _ArrayMapping]:
    m = KERNEL_RE.search(code)
    if not m:
        return code, []

    kname, param_block = m.group(1), m.group(2)
    new_params, mapping = [], []
    for raw in param_block.split(','):
        raw = raw.strip()
        mm = re.match(r"(\w+)\s*:\s*(\w+)\s*=\s*array((?:\[\d+])+)", raw)
        if not mm:
            new_params.append(raw)
            continue
        bname, typ, dims = mm.group(1), mm.group(2), mm.group(3)
        sizes = _expand_dimensions(dims)
        for idxs in _expand_combinations(sizes):
            sc_name = f"{bname}_{'_'.join(map(str, idxs))}"
            new_params.append(f"{sc_name}: {typ}")
            mapping.append((bname, idxs, sc_name))
    new_header = f"kernel {kname}({', '.join(new_params)}){{"
    return code.replace(m.group(0), new_header, 1), mapping


# ---------------------------------------------------------------------------
# 4) Substituir usos de arrays por variáveis escalares
# ---------------------------------------------------------------------------

def substitute_array_uses(code: str, mapping: _ArrayMapping) -> str:
    """Percorre o mapeamento (mais índices → primeiro) evitando colisões."""
    for base, idxs, sc in sorted(mapping, key=lambda t: -len(t[1])):
        idx_pat = ''.join(fr"\[\s*{i}\s*]" for i in idxs)
        code = re.sub(fr"\b{base}{idx_pat}", sc, code)
    return code

# ---------------------------------------------------------------------------
# 5) Unroll Loops
# ---------------------------------------------------------------------------
def unroll_for_loops(code: str) -> str:
    import textwrap

    def replace_indexed_vars(line: str) -> str:
        # Converte a[0][1] para a_0_1
        pattern = re.compile(r'(\w+)((?:\[\d+\])+)')
        def repl(m):
            name = m.group(1)
            indices = re.findall(r'\[(\d+)\]', m.group(2))
            return f"{name}_{'_'.join(indices)}"
        return pattern.sub(repl, line)

    def process_block(lines: list, loop_vars: dict) -> list:
        """Substitui as variáveis do loop por valores fixos e converte índices."""
        output = []
        for line in lines:
            for var, val in loop_vars.items():
                line = re.sub(rf'\b{var}\b', str(val), line)
            output.append(replace_indexed_vars(line))
        return output

    def collect_block(lines: list, start_idx: int, base_indent: int) -> tuple[list, int]:
        block = []
        i = start_idx
        while i < len(lines):
            line = lines[i]
            if line.strip() == "":
                block.append(line)
                i += 1
                continue
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent:
                break
            block.append(line)
            i += 1
        return block, i

    lines = code.splitlines()
    result = []
    i = 0

    stack = []

    while i < len(lines):
        line = lines[i]
        match = re.match(r'^(\s*)for\s+(\w+)\s+in\s+range\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*:', line)
        if match:
            indent, var, start, end = match.group(1), match.group(2), int(match.group(3)), int(match.group(4))
            base_indent = len(indent)
            body, next_i = collect_block(lines, i + 1, base_indent)
            new_result = []

            for val in range(start, end):
                loop_vars = {var: val}
                # Checar se a linha de loop seguinte também é um for
                body_unrolled = unroll_for_loops(textwrap.dedent("\n".join(body)))
                body_lines = body_unrolled.splitlines()
                body_replaced = process_block(body_lines, loop_vars)
                new_result.extend(body_replaced)

            result.extend(new_result)
            i = next_i
        else:
            result.append(line)
            i += 1

    return "\n".join(result)


# ---------------------------------------------------------------------------
# 6) Pipeline completo
# ---------------------------------------------------------------------------

def split_sil_and_cpu(source: str) -> tuple[str, str]:
    """Separa o código em duas partes: antes e depois do primeiro @cpu."""
    parts = re.split(r'(^\s*@cpu\b)', source, maxsplit=1, flags=re.MULTILINE)
    if len(parts) == 1:
        return source, ""
    sil_code = parts[0]
    cpu_tail = ''.join(parts[1:])  # inclui o @cpu em diante
    return sil_code, cpu_tail


def transform(source: str) -> str:
    sil_code, cpu_tail = split_sil_and_cpu(source)

    code, map_params = expand_kernel_parameters(sil_code)

    expanded, mapping_local = [], []
    for ln in code.splitlines():
        repl, mp = expand_array_declaration(ln)
        if repl is None:
            expanded.append(ln)
        else:
            expanded.append(repl)
            mapping_local.extend(mp)
    code = "\n".join(expanded)

    code = substitute_array_uses(code, map_params + mapping_local)

    code = unroll_for_loops(code)

    return code + "\n" + cpu_tail
