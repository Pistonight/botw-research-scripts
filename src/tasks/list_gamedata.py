"""
Process the GameData Flags (GameData/Flag)
"""

from dataclasses import dataclass
import yaml
import json
import os
import shutil
import util as u
import task as t
import spp

def task():
    inputs = {
        "game_data_dir": "botw/GameData/Flag",
        "game_data_placeholder": "botw/GameData/Flag/bool_data.yml",
    }

    outputs = {
        "game_data_dir": "output/GameData",
        "game_data_placeholder": "output/GameData/S32/dummy.yaml",
    }

    def run(inputs, outputs):
        return process_gamedata(
            inputs["game_data_dir"],
            outputs["game_data_dir"],
        )

    return t.task(__file__, inputs, outputs, run)

def process_gamedata(input_dir: str, output_dir: str) -> str | None:
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    def inputs(x):
        return [u.home(input_dir, y+".yml") for y in x]

    tasks = [
        (output_dir, inputs(["bool_array_data"]), "ArrayBool", "bool_array_data", "bool", True),
        (output_dir, inputs(["bool_data", "revival_bool_data"]), "Bool", "bool_data", "bool", False),
        (output_dir, inputs(["f32_array_data"]), "ArrayF32", "f32_array_data", "f32", True),
        (output_dir, inputs(["f32_data"]), "F32", "f32_data", "f32", False),
        (output_dir, inputs(["s32_array_data"]), "ArrayS32", "s32_array_data", "s32", True),
        (output_dir, inputs(["s32_data", "revival_s32_data"]), "S32", "s32_data", "s32", False),
        (output_dir, inputs(["string32_data"]), "String32", "string_data", "str", False),
        (output_dir, inputs(["string64_array_data"]), "ArrayString64", "string64_array_data", "str", True),
        (output_dir, inputs(["string64_data"]), "String64", "string64_data", "str", False),
        (output_dir, inputs(["string256_array_data"]), "ArrayString256", "string256_array_data", "str", True),
        (output_dir, inputs(["string256_data"]), "String256", "string256_data", "str", False),
        (output_dir, inputs(["vector2f_array_data"]), "ArrayVector2f", "vector2f_array_data", "vec2f", True),
        (output_dir, inputs(["vector2f_data"]), "Vector2f", "vector2f_data", "vec2f", False),
        (output_dir, inputs(["vector3f_array_data"]), "ArrayVector3f", "vector3f_array_data", "vec3f", True),
        (output_dir, inputs(["vector3f_data"]), "Vector3f", "vector3f_data", "vec3f", False),
        (output_dir, inputs(["vector4f_data"]), "Vector4f", "vector4f_data", "vec4f", False),
    ]

    progress = spp.printer(len(tasks), "Process GameData Flags")
    errors = []

    with u.pool() as pool:
        for (i, (name, err)) in enumerate(pool.imap_unordered(process_task, tasks)):
            if err:
                errors.append(err)
                continue
            progress.print(i + 1, name)
    progress.done()

    err = u.check_errors(errors)
    if err:
        return err

    return None

def process_task(args) -> tuple[str, str | None]:
    output_dir, inputs, output_name, top_prop_name, typ, is_array = args
    output_file = u.home(output_dir, output_name + ".yaml")

    output_data = []
    for input_file in inputs:
        err = process_file(input_file, top_prop_name, typ, is_array, output_data)
        if err: return output_name, err

    get_extras(output_name, output_data)
    output_data.sort(key=lambda x: x.hash)
    save_flag_file(output_data, output_file, typ)

    return output_name, None


# I really want the "worse" order but that's not the devs decided :<
PROP_R = 0x1 # Read
PROP_W = 0x2 # Write
PROP_S = 0x4 # Save
PROP_O = 0x8 # OneTrigger
PROP_E = 0x10 # EventAssociated

@dataclass
class FlagData:
    name: str = ""
    hash: int = 0
    prop_flags: str = ""
    min_val: str = ""
    max_val: str = ""
    init_value: str = ""
    length: int | None = None
    reset_type: int = 0

def make_bool_flag(name: str) -> FlagData:
    x = FlagData()
    x.name = name
    x.hash = u.crc32_signed(name)
    # we don't know, so just give all
    x.prop_flags = f"{u.hex08(PROP_E | PROP_S | PROP_R | PROP_O | PROP_W)} # eoswr"
    x.min_val = "false"
    x.max_val = "true"
    x.init_value = "false"
    x.length = None
    x.reset_type = 0
    return x

def make_s32_flag(name: str) -> FlagData:
    x = FlagData()
    x.name = name
    x.hash = u.crc32_signed(name)
    # we don't know, so just give all
    x.prop_flags = f"{u.hex08(PROP_E | PROP_S | PROP_R | PROP_O | PROP_W)} # eoswr"
    x.min_val = "0"
    x.max_val = "0"
    x.init_value = "0"
    x.length = None
    x.reset_type = 0
    return x

def make_f32_flag(name: str) -> FlagData:
    x = FlagData()
    x.name = name
    x.hash = u.crc32_signed(name)
    # we don't know, so just give all
    x.prop_flags = f"{u.hex08(PROP_E | PROP_S | PROP_R | PROP_O | PROP_W)} # eoswr"
    x.min_val = "0.0"
    x.max_val = "0.0"
    x.init_value = "0.0"
    x.length = None
    x.reset_type = 0
    return x


def get_extras(output: str, out: list[FlagData]):
    if output == "ArrayBool":
        return
    if output == "Bool":
        out.append(make_bool_flag("AoC_DragonFireChallengeRing_Advent"))
        out.append(make_bool_flag( "AoC_RandomSpawnTreasure_IsRandomized",))
        out.append(make_bool_flag( "AoC_TestProg_Imoto_Flag_00"))
        out.append(make_bool_flag( "AocTestEx_Omosako_IsPastWorld"))
        out.append(make_bool_flag( "SpurGear_revolve_01"))
        out.append(make_bool_flag( "SpurGear_revolve_02"))
        return
    if output == "S32":
        out.append(make_s32_flag("AoC_TestProg_Imoto_TagCount_00"));
        out.append(make_s32_flag("AocTestEx_Omosako_SandOfTime_Num"));
        out.append(make_s32_flag("Location_DarkDungeon01"));
        out.append(make_s32_flag("Location_DarkDungeon02"));
        out.append(make_s32_flag("Location_DarkDungeon03"));
        out.append(make_s32_flag("Location_DarkDungeon04"));
        return;
    if output == "F32":
        out.append(make_f32_flag("AocTestEx_Omosako_ReturnToMainField_Rotation"));
        out.append(make_f32_flag("AocTestEx_Omosako_SandOfTime_Rate"));
        return
    if output == "ArrayString64":
        x = FlagData()
        x.name = "AoC_RandomSpawnTreasure_Contents"
        x.hash = u.crc32_signed(x.name)
        x.prop_flags = f"{u.hex08(PROP_E | PROP_S | PROP_R | PROP_O | PROP_W)} # eoswr"
        x.min_val = "\"\""
        x.max_val = "\"\""
        x.init_value = "[\"\"]"
        x.length = 1
        x.reset_type = 0
        out.append(x)
        return
    if output == "Vector3f":
        x = FlagData()
        x.name = "AocTestEx_Omosako_ReturnToMainField_Rotation"
        x.hash = u.crc32_signed(x.name)
        x.prop_flags = f"{u.hex08(PROP_E | PROP_S | PROP_R | PROP_O | PROP_W)} # eoswr"
        x.min_val = "[0.0,0.0,0.0]"
        x.max_val = "[0.0,0.0,0.0]"
        x.init_value = "[0.0,0.0,0.0]"
        x.length = None
        x.reset_type = 0
        out.append(x)
        return

def process_file(
    input_file: str, 
    top_prop_name: str, # i.e. bool_array_data
    typ: str, # i.e. bool
    is_array: bool,
    output_data: list[FlagData]
) -> str | None:
    data, err = u.fyaml(input_file)
    if err: return err
    flag_array, err = u.sfget(data, top_prop_name, list)
    if err: return err

    for flag_data in flag_array:
        flag, err = parse_flag(flag_data, typ, is_array)
        if err: return err
        output_data.append(flag)

    return None

def parse_flag(flag_data, typ: str, is_array: bool) -> tuple[FlagData, str | None]:
    x = FlagData()
    name, hash, err = get_name_hash_checked(flag_data)
    if err: return x, err
    err = common_check(name, flag_data)
    if err: return x, err

    prop_flags, err = get_property_flag_checked(name, flag_data)
    if err: return x, err
    min_val, max_val, err = format_min_max_checked(name, flag_data, typ)
    if err: return x, err

    length = None
    if is_array:
        init_value, length, err = get_init_value_array_and_length_checked(name, flag_data, typ)
    else:
        init_value, err = get_init_value_checked(name, flag_data, typ)
    if err: return x, err

    reset_type, err = u.sfget(flag_data, "ResetType", int)
    if (reset_type < 0 or reset_type > 4):
        return x, f"invalid ResetType for flag {name}: {reset_type}"
    if err: return x, err
    x.name = name
    x.hash = hash
    x.prop_flags = prop_flags
    x.min_val = min_val
    x.max_val = max_val
    x.init_value = init_value
    x.length = length
    x.reset_type = reset_type
    return x, None

def common_check(name, flag_data) -> str | None:
    delete_rev, err = u.sfget(flag_data, "DeleteRev", int)
    if err: return err
    if delete_rev != -1:
        return f"invalid DeleteRev for flag {name}: {delete_rev}"
    return None

def get_name_hash_checked(flag_data) -> tuple[str, int, str | None]:
    name, err = u.sfget(flag_data, "DataName", str)
    if err: return "", 0, err
    if not name:
        return "", 0, "invalid empty flag name"
    hash_loaded, err = u.sfget(flag_data, "HashValue", int)
    if err: return "", 0, f"failed to load hash for flag {name}"
    hash_computed = u.crc32_signed(name)
    if hash_loaded != hash_computed:

        # this is a special case .. for some reason
        if name == "dummy" and hash_loaded == 1000:
            return name, hash_loaded, None

        return "", 0, f"hash mismatch for flag {name}: {u.hex08(hash_loaded)} != {u.hex08(hash_computed)}"
    return name, hash_loaded, None

def get_property_flag_checked(name, flag_data) -> tuple[str, str | None]:
    int_repr = 0;
    str_repr = "";

    is_read, err = u.sfget(flag_data, "IsProgramReadable", bool)
    if err: return "", err
    if is_read:
        int_repr |= PROP_R
        str_repr += "r"
    else:
        str_repr += "-"

    is_write, err = u.sfget(flag_data, "IsProgramWritable", bool)
    if err: return "", err
    if is_write:
        int_repr |= PROP_W
        str_repr += "w"
    else:
        str_repr += "-"

    is_save, err = u.sfget(flag_data, "IsSave", bool)
    if err: return "", err
    if is_save:
        int_repr |= PROP_S
        str_repr += "s"
    else:
        str_repr += "-"

    is_one_trigger, err = u.sfget(flag_data, "IsOneTrigger", bool)
    if err: return "", err
    if is_one_trigger:
        int_repr |= PROP_O
        str_repr += "o"
    else:
        str_repr += "-"

    is_event_associated, err = u.sfget(flag_data, "IsEventAssociated", bool)
    if err: return "", err
    if is_event_associated:
        int_repr |= PROP_E
        str_repr += "e"
    else:
        str_repr += "-"

    return f"0x{int_repr:02x} # {str_repr}", None

def format_min_max_checked(name, flag_data, typ: str) -> tuple[str, str, str | None]:
    min_val, err = u.sfgetany(flag_data, "MinValue")
    if err: return "", "", err
    max_val, err = u.sfgetany(flag_data, "MaxValue")
    if err: return "", "", err

    if typ == "bool":
        if min_val != False or max_val != True:

            # only this flag has false, false for some reason
            if name == "Find_4Relic_2ndClear":
                if min_val != False or max_val != False:
                    return "", "", f"invalid bool range for flag {name}"
                return "false", "false", None

            return "", "", f"invalid bool range for flag {name}"
        return "false", "true", None

    if typ == "f32":
        min_val, err = stringify_checked(name, min_val, "f32")
        if err: return "", "", f"invalid f32 min_val for flag {name}: {err}"
        max_val, err = stringify_checked(name, max_val, "f32")
        if err: return "", "", f"invalid f32 max_val for flag {name}: {err}"

        return min_val, max_val, None

    if typ == "s32":
        if not isinstance(min_val, int) or not isinstance(max_val, int):
            return "", "", f"invalid s32 range for flag {name}"
        return str(min_val), str(max_val), None

    if typ == "str":
        if min_val != "" or max_val != "":
            return "", "", f"invalid str range for flag {name}. str range must be empty string"
        return "\"\"", "\"\"", None

    if typ == "vec2f":
        if not isinstance(min_val, list) or not isinstance(max_val, list):
            return "", "", f"invalid vec2f range for flag {name}"
        min_val = min_val[0]
        max_val = max_val[0]
        min_formated, err = format_float_vec_checked(name, min_val, 2)
        if err: return "", "", f"invalid vec2f range for flag {name}: {err}"
        max_formated, err = format_float_vec_checked(name, max_val, 2)
        if err: return "", "", f"invalid vec2f range for flag {name}: {err}"

        return min_formated, max_formated, None

    if typ == "vec3f":
        if not isinstance(min_val, list) or not isinstance(max_val, list):
            return "", "", f"invalid vec2f range for flag {name}"
        min_val = min_val[0]
        max_val = max_val[0]
        min_formated, err = format_float_vec_checked(name, min_val, 3)
        if err: return "", "", f"invalid vec3f range for flag {name}: {err}"
        max_formated, err = format_float_vec_checked(name, max_val, 3)
        if err: return "", "", f"invalid vec3f range for flag {name}: {err}"

        return min_formated, max_formated, None

    if typ == "vec4f":
        if not isinstance(min_val, list) or not isinstance(max_val, list):
            return "", "", f"invalid vec2f range for flag {name}"
        min_val = min_val[0]
        max_val = max_val[0]
        min_formated, err = format_float_vec_checked(name, min_val, 4)
        if err: return "", "", f"invalid vec4f range for flag {name}: {err}"
        max_formated, err = format_float_vec_checked(name, max_val, 4)
        if err: return "", "", f"invalid vec4f range for flag {name}: {err}"

        return min_formated, max_formated, None

    return "", "", f"invalid type {typ} for flag {name}"

def get_init_value_checked(name, flag_data, typ: str) -> tuple[str, str | None]:
    if typ.startswith("vec"):
        init_value, err = u.sfget(flag_data, "InitValue", list)
        if err: return "", f"cannot get InitValue for vec type flag {name}: {err}"
        if len(init_value) != 1:
            return "", f"invalid {typ} array for flag {name} init value (wrong length, should be 1)"
        init_value = init_value[0]
    else:
        init_value, err = u.sfgetany(flag_data, "InitValue")
        if err: return "", f"cannot get InitValue for flag {name}: {err}"

    return stringify_checked(name, init_value, typ)


def get_init_value_array_and_length_checked(name, flag_data, typ: str) -> tuple[str, int, str | None]:
    init_value, err = u.sfget(flag_data, "InitValue", list)
    if err: return "", 0, f"cannot get InitValue for array type flag {name}: {err}"
    if len(init_value) != 1:
        return "", 0, f"invalid {typ} array for flag {name} init value (wrong length, should be 1)"
    init_value = init_value[0]
    init_value, err = u.sfget(init_value, "Values", list)
    if err: return "", 0, f"invalid {typ} array for flag {name} init value (bad format)"
    length = len(init_value)

    values = []
    for x in init_value:
        if typ.startswith("vec"):
            if not isinstance(x, list):
                return "", 0, f"invalid {typ} array for flag {name} (vec wrapper)"
            if len(x) != 1:
                return "", 0, f"invalid {typ} array for flag {name} (vec wrapper wrong length)"
            x = x[0]
        formatted, err = stringify_checked(name, x, typ)
        if err: return "", 0, f"invalid {typ} array for flag {name} (bad element format): {err}"
        values.append(formatted)

    return f"[{','.join(values)}]", length, None

def stringify_checked(name, x, typ: str) -> tuple[str, str | None]:
    if typ == "bool":
        if not isinstance(x, bool):
            if not isinstance(x, int):
                return "", f"invalid {typ} array for flag {name} (not bool)"
            if x != 1 and x % 2 == 1:
                return "", f"invalid {typ} array for flag {name} (not bool)"
            return "true" if x  == 1 else "false", None
        return "true" if x  else "false", None
    if typ == "f32":
        if not isinstance(x, float):
            if not isinstance(x, int):
                return "", f"invalid {typ} array for flag {name} (not float)"
            return str(float(x)), None
        return str(x), None
    if typ == "s32":
        if not isinstance(x, int):
            return "", f"invalid {typ} array for flag {name} (not int)"
        return str(x), None
    if typ == "str":
        if not isinstance(x, str):
            return "", f"invalid {typ} array for flag {name} (not str)"
        return f"{json.dumps(x)}", None
    if typ == "vec2f":
        x, err = format_float_vec_checked(name, x, 2)
        if err: return "", f"invalid {typ} array for flag {name} (not vec2f): {err}"
        return x, None
    if typ == "vec3f":
        x, err = format_float_vec_checked(name, x, 3)
        if err: return "", f"invalid {typ} array for flag {name} (not vec3f): {err}"
        return x, None
    if typ == "vec4f":
        x, err = format_float_vec_checked(name, x, 4)
        if err: return "", f"invalid {typ} array for flag {name} (not vec4f): {err}"
        return x, None
    return "", f"invalid type {typ} for flag {name}"

def format_float_vec_checked(name, data, dim: int) -> tuple[str, str | None]:
    if not isinstance(data, list):
        return "", f"invalid float vec {name} (not list)"
    if len(data) != dim:
        return "", f"invalid float vec {name} (wrong length)"
    for i in range(dim):
        if not isinstance(data[i], float):
            return "", f"invalid {name} (not float)"
    return "[" + ",".join([str(x) for x in data]) + "]", None

def save_flag_file(data: list[FlagData], file: str, typ: str) -> str | None:
    with u.fopenw(file) as f:
        for x in data:
            f.write(f"- name: {x.name}\n")
            f.write(f"  hash: {u.hex08(x.hash)}\n")
            f.write(f"  prop_flags: {x.prop_flags}\n")
            if typ != "str" and typ != "bool":
                f.write(f"  min: {x.min_val}\n")
                f.write(f"  max: {x.max_val}\n")
            if x.length is not None:
                # compact initial format
                if x.init_value.startswith("[") and x.init_value.endswith("]"):
                    all_same = True
                    init_value_arr = yaml.safe_load(x.init_value)
                    first = init_value_arr[0]
                    for i in range(1, x.length):
                        if first != init_value_arr[i]:
                            all_same = False
                            break
                    if all_same:
                        f.write(f"  initial: [{json.dumps(first)}]\n")
                    else:
                        f.write(f"  initial: {x.init_value}\n")
                f.write(f"  len: {x.length}\n")
            else:
                f.write(f"  initial: {x.init_value}\n")
            f.write(f"  reset_type: {x.reset_type} # {reset_type_desc(x.reset_type)}\n")
        
def reset_type_desc(t):
    if t == 0:
        return "no-reset"
    if t == 1:
        return "reset-on-bloodmoon"
    if t == 2:
        return "reset-on-stage-generation"
    if t == 3:
        return "reset-at-midnight"
    if t == 4:
        return "reset-on-animal-master-appearance"
    return "???"
    
