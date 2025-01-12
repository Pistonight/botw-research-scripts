"""
Decode the System section in CookData.yaml, which contains
parameters for CookEffects
"""

import util as u
import task as t

def task():
    inputs = {
        "cook_data_path": "botw/Cooking/CookData.yml",
    }

    outputs = {
        "system_save_path": "output/cook-system.yaml",
    }

    def run(inputs, outputs):
        return decode_cook_system(inputs["cook_data_path"], outputs["system_save_path"])

    return t.task(__file__, inputs, outputs, run)

EFFECTS = [
    "StaminaRecover",
    "GutsPerformance",
    "LifeRecover",
    "LifeMaxUp",
    "ResistHot",
    "ResistCold",
    "ResistElectric",
    "AllSpeed",
    "AttackUp",
    "DefenseUp",
    "Quietness",
    "Fireproof",
]

def decode_effect(hash: int) -> tuple[str, str | None]:
    for effect in EFFECTS:
        if u.crc32(effect) == hash:
            return effect, None
    return "", f"unknown effect with hash {u.hex08(hash)}"

def decode_f32(value: float) -> tuple[str, str | None]:
    if value == 1.39999997615814208984375:
        return "0x3fb33333 # 1.4f32", None
    if value == 0.5:
        return "0x3f000000 # 0.5f32", None
    if value == 2.0:
        return "0x40000000 # 2.0f32", None
    if value == 1.0:
        return "0x3f800000 # 1.0f32", None
    if value == 1.5:
        return "0x3fc00000 # 1.5f32", None
    if value == 0.3499999940395355224609375:
        return "0x3eb33333 # 0.35f32", None
    if value == 0.449999988079071044921875:
        return "0x3ee66666 # 0.45f32", None
    if value == 0.300000011920928955078125:
        return "0x3e99999a # 0.3f32", None
    if value == 1.7999999523162841796875:
        return "0x3fe66666 # 1.8f32", None
    if value == 2.099999904632568359375:
        return "0x40066666 # 2.1f32", None
    if value == 2.400000095367431640625:
        return "0x4019999a # 2.4f32", None
    if value == 2.7999999523162841796875:
        return "0x40333333 # 2.8f32", None
    return "", f"unknown f32 value {value}"


def decode_cook_system(cook_data_path: str, system_save_path: str) -> str | None:
    data, err = u.fyaml(cook_data_path)
    if err: return err
    
    system, err = u.sfget(data, "System", dict)
    if err: return err
    cei, err = u.sfget(system, "CEI", list)
    if err: return err
    for entry in cei:
        effect, err = decode_effect(entry["T"])
        if err: return err
        entry["T"] = effect
    # Save System
    KEYWORDS = """
# Keys are based on guesses from the data and decomp
# CEI:    cook_effect_index
# BT:     base_time
# MR:     multiplier
# Ma:     max
# Mi:     min
# SSA:    super_success_amount
# T:      type
# FA:     failure_actor
# FALR:   faliure_actor_life_recover
# FALRMR: faliure_actor_life_recover_multiplier
# FCA:    fairy_cook_actor
# LRMR:   life_recover_multiplier
# MEA:    monster_extract_actor
# NMMR:   num_matrial_multiplier
# NMSSR:  num_material_super_success_rate
# SFALR:  stone_food_actor_life_recover
# SSAET:  super_success_additional_effect_time
"""
    with u.fopenw(system_save_path) as f:
        f.write(KEYWORDS)
        f.write("cook_effect_index:\n")
        for entry in cei:
            f.write(f"  - {{ type: {entry["T"] + ",":<24} base_time: {entry["BT"]:<10},\n")
            f.write(f"      max: {entry["Ma"]:<3}, min: {entry["Mi"]:<3}, super_success_amount: {entry["SSA"]:<10},\n")
            multiplier, err = decode_f32(entry["MR"])
            multiplier, comment = multiplier.split("#")
            if err: return err
            f.write(f"      multiplier: {(multiplier + "} #" + comment )}\n")
        f.write(f"failure_actor: {system["FA"]}\n")
        f.write(f"failure_actor_life_recover: {system["FALR"]}\n")
        f.write(f"failure_actor_life_recover_multiplier: {system["FALRMR"]}\n")
        f.write(f"fairy_cook_actor: {system["FCA"]}\n")
        f.write(f"life_recover_multiplier: {system["LRMR"]}\n")
        f.write(f"monster_extract_actor: {system["MEA"]}\n")
        f.write(f"num_material_multiplier:\n")
        for entry in system["NMMR"]:
            value, err = decode_f32(entry)
            if err: return err
            f.write(f"  - {value}\n")
        f.write(f"num_material_super_success_rate: {system["NMSSR"]}\n")
        f.write(f"stone_food_actor_life_recover: {system["SFALR"]}\n")
        f.write(f"super_success_additional_effect_time: {system["SSAET"]}\n")

    print(f"Saved CookData.System to {u.relpath(system_save_path)}")

