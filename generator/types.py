def generate_builtin_types(self):
    """
    Generates all core SPIR-V types required by Sil:
    - void, bool, uint, float
    - pointers for Function and CrossWorkgroup storage classes

    Stores their SPIR-V IDs in self.type_ids and returns the corresponding
    SPIR-V type declarations as a list of strings.

    Returns:
        list[str]: SPIR-V type declarations.
    """
    types = []

    # Scalar types
    void_type = self.new_id()
    bool_type = self.new_id()
    uint_type = self.new_id()
    float_type = self.new_id()

    # Register scalar type IDs
    self.type_ids['void'] = void_type
    self.type_ids['bool'] = bool_type
    self.type_ids['uint'] = uint_type
    self.type_ids['int'] = uint_type  # alias
    self.type_ids['float'] = float_type

    # SPIR-V type definitions
    types.append(f"{void_type} = OpTypeVoid")
    types.append(f"{bool_type} = OpTypeBool")
    types.append(f"{uint_type} = OpTypeInt 32 0")  # unsigned 32-bit int
    types.append(f"{float_type} = OpTypeFloat 32")  # 32-bit float

    # CrossWorkgroup pointers (used for kernel inputs/outputs)
    for base in ["int", "uint", "float", "bool"]:
        ptr_id = self.new_id()
        self.type_ids[f'ptr_cross_{base}'] = ptr_id
        types.append(f"{ptr_id} = OpTypePointer CrossWorkgroup {self.type_ids[base]}")
        self.type_ids[f'ptr_{base}'] = ptr_id  # alias for convenience

    # Function-local pointers
    for base in ["int", "uint", "float", "bool"]:
        ptr_id = self.new_id()
        self.type_ids[f'ptr_func_{base}'] = ptr_id
        types.append(f"{ptr_id} = OpTypePointer Function {self.type_ids[base]}")

    return types


def get_constant(self, value):
    """
    Returns a SPIR-V constant ID for a given literal value.
    If already declared, returns the existing ID. Otherwise, defines it.

    Args:
        value (int or float): The constant value.

    Returns:
        str: SPIR-V ID of the constant.
    """
    value_str = str(value)

    if value_str in self.constants:
        return self.constants[value_str].split('=')[0].strip()

    const_id = self.new_id()
    base_type = self.type_ids['uint'] if isinstance(value, int) else self.type_ids['float']

    self.constants[value_str] = f"{const_id} = OpConstant {base_type} {value}"
    return const_id


def get_constant_false(self):
    """
    Returns a constant ID for 'false' (OpConstantFalse).
    Only created once and cached.

    Returns:
        str: SPIR-V ID for boolean false.
    """
    if "false" not in self.constants:
        const_id = self.new_id()
        self.constants["false"] = f"{const_id} = OpConstantFalse {self.type_ids['bool']}"

    return self.constants["false"].split('=')[0].strip()
