def expand_array_reference(base_name, rows, cols, declared_type):
    expanded = []
    for i in range(rows):
        for j in range(cols):
            name = f"{base_name}_{i}_{j}"
            expanded.append((name, declared_type))
    return expanded
