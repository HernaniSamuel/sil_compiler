def generate_builtin_types(self):
    types = []

    void_type = self.new_id()
    bool_type = self.new_id()
    uint_type = self.new_id()
    float_type = self.new_id()

    self.type_ids['void'] = void_type
    self.type_ids['bool'] = bool_type
    self.type_ids['uint'] = uint_type
    self.type_ids['int'] = uint_type  # alias
    self.type_ids['float'] = float_type

    types.append(f"{void_type} = OpTypeVoid")
    types.append(f"{bool_type} = OpTypeBool")
    types.append(f"{uint_type} = OpTypeInt 32 0")
    types.append(f"{float_type} = OpTypeFloat 32")

    # Ponteiros CrossWorkgroup
    for base in ["int", "uint", "float", "bool"]:
        ptr_id = self.new_id()
        self.type_ids[f'ptr_cross_{base}'] = ptr_id
        types.append(f"{ptr_id} = OpTypePointer CrossWorkgroup {self.type_ids[base]}")
        self.type_ids[f'ptr_{base}'] = ptr_id  # alias

    # Ponteiros Function
    for base in ["int", "uint", "float", "bool"]:
        ptr_id = self.new_id()
        self.type_ids[f'ptr_func_{base}'] = ptr_id
        types.append(f"{ptr_id} = OpTypePointer Function {self.type_ids[base]}")

    return types

def get_constant(self, value):
    value_str = str(value)
    if value_str in self.constants:
        return self.constants[value_str].split('=')[0].strip()
    const_id = self.new_id()
    if isinstance(value, int):
        base_type = self.type_ids['uint']  # sempre unsigned agora
    else:
        base_type = self.type_ids['float']
    self.constants[value_str] = f"{const_id} = OpConstant {base_type} {value}"

    return const_id

def get_constant_false(self):
    if "false" not in self.constants:
        const_id = self.new_id()
        self.constants["false"] = f"{const_id} = OpConstantFalse {self.type_ids['bool']}"
    return self.constants["false"].split('=')[0].strip()
