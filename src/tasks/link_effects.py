"""
Link CookEffect, WeaponModifier, and SpecialStatus objects
"""
import os
import json
import util as u
import task as t
import spp
import msyt

def task():
    inputs = {
        "messages": "botw/Message",
        "cook_system_path": "output/cook-system.yaml",
    }

    outputs = {
        "special_status_dir": "output/SpecialStatus",
        "cook_effect_dir": "output/CookEffect",
    }

    def run(_, outputs):
        err = save_special_status(outputs["special_status_dir"])
        if err: return err
        err = save_cook_effects(outputs["cook_effect_dir"], inputs["cook_system_path"])
        if err: return err

        return None

    return t.task(__file__, inputs, outputs, run)

# This is the effect displayed on the player/weapon
# Could come from:
#   - Weapon modifier
#   - Meal effect
#   - Armor effect
# Ordered by appearance in SpecialStatus.myst
SPECIAL_STATUS_TABLE = [
    "AddGuardPlus", # (wpmod) Yellow Shield Guard Up
    "AddGuard", # (wpmod) Blue Shield Guard Up
    "AddLifePlus", # (wpmod) Yellow Durability Up
    "AddLife", # (wpmod) Blue Durability Up
    "AddPowerPlus", # (wpmod) Yellow Attack Up
    "AddPower", # (wpmod) Blue Attack Up
    "AllSpeed", # (meal) Movement Speed Up
    "AttackUp", # (meal/armor) Attack Up
    # -- The CompletionBonus (armor set bonus) are skipped
    "ClimbSpeedUp", # (armor) Climbing Speed Up
    "Critical", # (wpmod) Critical Hit
    "DefenseUp", # (meal) Defense Up
    "ExGutsMaxUp", # (meal) Endura
    "Fireproof", # (meal) Fireproof // I think set bonus is also this?
    "GutsRecover", # (meal) Stamina recover
    "LifeMaxUp", # (meal) Hearty/yellow hearts
    "LongThrow", # (wpmod) Long Throw
    "Quietness", # (meal/armor) Stealth Up
    "RapidFire", # (wpmod) Quick Shot
    "ReduceAncientEnemyDamge", # (armor) ancient/ diamond circlet/midna, didn't spell wrong
    "ResistCold", # (meal/armor) Cold Resistance
    "ResistElectric", # (meal/armor) Shock Resistance
    "ResistFreeze", # (armor) unfreezable
    "ResistHot", # (meal/armor) Heat Resistance
    "ResistLightning", # (armor) Lightning Proof
    "SandMoveSpeedUp", # (armor) Sand Speed Up
    "SnowMovingSpeed", # (armor) Snow Speed Up
    "SpreadFire", # (wpmod) Multi-Shot
    "SurfMaster", # (wpmod) Shield surf friction minus
    "SwimSpeedUp", # (armor) Swim Speed Up
]
# For CookData.System, see:
#   - https://github.com/Pistonite/botw-recipe/blob/main/research/output/cookdata-system.yaml
#     which is decoded from Cooking/CookData.yaml from leoetlino/botw
# For code values, see cookManager.cpp and cookManager.h in botw decomp
# Ordered by CookData.System
#
# Note that LifeRecover has no translation entry
COOK_EFFECTS = [
    # Name that corres- # Effect name in  # Effect name in  # CookEffectId
    # ponds to hash in    translation       code
    # CookData.System     files                                 # Corresponding SpecialStatus
    #                     (used as name)
    ["StaminaRecover",  "GutsRecover",    "GutsRecover",    14, "GutsRecover"],
    ["GutsPerformance", "ExGutsMaxUp",    "ExGutsMaxUp",    15, "ExGutsMaxUp"],
    ["LifeRecover",     "LifeRecover",    "LifeRecover",    1 , None],
    ["LifeMaxUp",       "LifeMaxUp",      "LifeMaxUp",      2 , "LifeMaxUp"],
    ["ResistHot",       "ResistHot",      "ResistHot",      4 , "ResistHot"],
    ["ResistCold",      "ResistCold",     "ResistCold",     5 , "ResistCold"],
    ["ResistElectric",  "ResistElectric", "ResistElectric", 6 , "ResistElectric"],
    ["AllSpeed",        "AllSpeed",       "MovingSpeed",    13, "AllSpeed"],
    ["AttackUp",        "AttackUp",       "AttackUp",       10, "AttackUp"],
    ["DefenseUp",       "DefenseUp",      "DefenseUp",      11, "DefenseUp"],
    ["Quietness",       "Quietness",      "Quietness",      12, "Quietness"],
    ["Fireproof",       "Fireproof",      "Fireproof",      16, "Fireproof"],
]
def get_cook_effect_for_special_status(special_status: str):
    for _, cook_effect, _, _, ss in COOK_EFFECTS:
        if ss == special_status:
            return cook_effect
    return None
# [ 
#     internal name,  <- used as name
#     botw decomp name (WeaponModifier), 
#     code value, 
#     SpecialStatus name
#     Yellow Special Status name
# ]
WEAPON_MODIFIERS = [
    # Internal Name # Decomp name    # Value # SpecialStatus # Yellow SpecialStatus
    ["None",        "None",          0,     None,         None],
    ["AddPower",    "AddAtk",        0x1,   "AddPower",   "AddPowerPlus"],
    ["AddLife",     "AddLife",       0x2,   "AddLife",    "AddLifePlus"],
    ["Critical",    "AddCrit",       0x4,   "Critical",   "Critical"],
    ["LongThrow",   "AddThrow",      0x8,   "LongThrow",  "LongThrow"],
    ["SpreadFire",  "AddSpreadFire", 0x10,  "SpreadFire", "SpreadFire"],
    ["Zoom",        "AddZoomRapid",  0x20,  None,         None],
    ["RapidFire",   "AddRapidFire",  0x40,  "RapidFire",  "RapidFire"],
    ["SurfMaster",  "AddSurfMaster", 0x80,  "SurfMaster", "SurfMaster"],
    ["AddGuard",    "AddGuard",      0x100, "AddGuard",   "AddGuardPlus"],
]
def get_weapon_modifier_for_special_status(special_status):
    for wm_name, _, _, ss, ss_yellow in WEAPON_MODIFIERS:
        if ss == special_status or ss_yellow == special_status:
            return wm_name
    return None

def _static_msg_file(locale_nin, file):
    return u.botw("Message", f"Msg_{locale_nin}.product.sarc", "StaticMsg", file)

def save_special_status(special_status_dir: str) -> str | None:
    progress = spp.printer(0, "Load SpecialStatus.msyt")
    count = 0
    special_status_localization = {}
    for locale, locale_nin in msyt.locale_map.items():
        data, err = u.fyaml(_static_msg_file(locale_nin, "SpecialStatus.msyt"))
        if err: return err
        entries_data, err = u.sfget(data, "entries", dict)
        if err: return err
        for name, data in entries_data.items():
            err = u.ensure(name.endswith("_Name"), f"SpecialStatus entry must end in _Name: {name}")
            if err: return err
            special_status_name = name[:-5]
            count += 1
            progress.print(count, f"{locale}: {special_status_name}")
            if special_status_name not in special_status_localization:
                special_status_localization[special_status_name] = {}
            text, _, err = msyt.parse_localization(data, False)
            if err: return err
            special_status_localization[special_status_name][locale] = text
    # Patch the localization for SurfMaster in the Chinese languages
    # The game file just uses the JP translation since the effect is unused
    special_status_localization["SurfMaster"]["zh-CN"] = "\u76fe\u6ed1\u884c\u63d0\u5347"
    special_status_localization["SurfMaster"]["zh-TW"] = "\u76fe\u6ed1\u884c\u63d0\u5347"

    progress.done()
    u.clean_dir(special_status_dir)
    for special_status in SPECIAL_STATUS_TABLE:
        with u.fopenw(os.path.join(special_status_dir, f"{special_status}.yaml")) as f:
            f.write(f"name: {special_status}\n")
            cook_effect = get_cook_effect_for_special_status(special_status)
            if cook_effect:
                f.write(f"cook_effect: {cook_effect}\n")
            else:
                f.write("cook_effect: null\n")
            weapon_modifier = get_weapon_modifier_for_special_status(special_status)
            if weapon_modifier:
                f.write(f"weapon_modifier: {weapon_modifier}\n")
            else:
                f.write("weapon_modifier: null\n")
            f.write("localization:\n")
            for locale in msyt.locale_map:
                text = special_status_localization[special_status][locale]
                f.write(f"  {locale}: {json.dumps(text)}\n")
    # Special file for zoom
    ZOOM_STATUS = """
name: Zoom
cook_effect: null
weapon_modifier: Zoom
localization:
  en-US: "Zoom"
  ja-JP: "\\u30ba\\u30fc\\u30e0"
  de-DE: "Zoom"
  es-ES: "Zoom"
  it-IT: "Zoom"
  fr-FR: "Zoom"
  ru-RU: "\\u0431\\u0435\\u043a\\u0430\\u0441"
  zh-CN: "\\u500d\\u955c"
  zh-TW: "\\u500d\\u93e1"
  ko-KR: "\\ub3cb\\ubcf4\\uae30"
  nl-NL: "Zoom"
"""
    with u.fopenw(os.path.join(special_status_dir, "Zoom.yaml")) as f:
        f.write(ZOOM_STATUS)

    # plus one for zoom
    print(f"Saved {len(SPECIAL_STATUS_TABLE) + 1} SpecialStatus")
    return None

def save_cook_effects(cook_effect_dir: str, cook_system_path: str) -> str | None:
    progress = spp.printer(0, "Load CookEffect.msyt")
    count = 0
    cook_effect_localization = {}
    for locale, locale_nin in msyt.locale_map.items():
        data, err = u.fyaml(_static_msg_file(locale_nin, "CookEffect.msyt"))
        if err: return err
        entries_data, err = u.sfget(data, "entries", dict)
        if err: return err
        for name, data in entries_data.items():
            count += 1
            progress.print(count, f"{locale}: {name}")
            parts = name.split("_", 1)
            effect_name = parts[0]
            rest = parts[1] if len(parts) > 1 else ""
            if effect_name not in cook_effect_localization:
                cook_effect_localization[effect_name] = {}
                for l in msyt.locale_map:
                    cook_effect_localization[effect_name][l] = {}
            if rest == "Name":
                text, _, err = msyt.parse_localization(data, False)
                if err:
                    return f"error parsing localization for {name}: {err}"
                cook_effect_localization[effect_name][locale]["name"] = text
            elif rest == "Name_Feminine":
                text, _, err = msyt.parse_localization(data, False)
                if err:
                    return f"error parsing localization for {name}: {err}"
                cook_effect_localization[effect_name][locale]["name_feminine"] = text
            elif rest == "Name_Masculine":
                text, _, err = msyt.parse_localization(data, False)
                if err:
                    return f"error parsing localization for {name}: {err}"
                cook_effect_localization[effect_name][locale]["name_masculine"] = text
            elif rest == "Name_Neuter":
                text, _, err = msyt.parse_localization(data, False)
                if err:
                    return f"error parsing localization for {name}: {err}"
                cook_effect_localization[effect_name][locale]["name_neuter"] = text
            elif rest == "Name_Plural":
                text, _, err = msyt.parse_localization(data, False)
                if err:
                    return f"error parsing localization for {name}: {err}"
                cook_effect_localization[effect_name][locale]["name_plural"] = text
            elif rest.startswith("Desc"):
                parts = rest.split("_", 1)
                desc_level = (int(parts[1]) - 1) if len(parts) > 1 else 0
                if "desc" not in cook_effect_localization[effect_name][locale]:
                    cook_effect_localization[effect_name][locale]["desc"] = []
                desc_array = cook_effect_localization[effect_name][locale]["desc"]
                if len(desc_array) <= desc_level:
                    desc_array.extend([""] * (desc_level - len(desc_array) + 1))
                text, _, err = msyt.parse_localization(data, False)
                if err:
                    return f"error parsing localization for {name}: {err}"
                desc_array[desc_level] = text
            elif rest.startswith("MedicineDesc"):
                parts = rest.split("_", 1)
                desc_level = (int(parts[1]) - 1) if len(parts) > 1 else 0
                if "elixir_desc" not in cook_effect_localization[effect_name][locale]:
                    cook_effect_localization[effect_name][locale]["elixir_desc"] = []
                desc_array = cook_effect_localization[effect_name][locale]["elixir_desc"]
                if len(desc_array) <= desc_level:
                    desc_array.extend([""] * (desc_level - len(desc_array) + 1))
                text, _, err = msyt.parse_localization(data, False)
                desc_array[desc_level] = text
            else:
                return f"Unknown cook effect entry in {name}"

    progress.done()

    system, err = u.fyaml(cook_system_path)
    if err: return err
    cei = system["cook_effect_index"]
    cei_map = {}
    for entry in cei:
        cei_map[entry["type"]] = entry

    u.clean_dir(cook_effect_dir)
    for system_name, name, code_name, value, special_status in COOK_EFFECTS:
        with u.fopenw(os.path.join(cook_effect_dir, f"{name}.yaml")) as f:
            f.write(f"name: {name}\n")
            f.write("# Cooking/CookData.byml System\n")
            f.write(f"system_name: {system_name}\n")
            effect_entry, err = u.sfget(cei_map, system_name, dict)
            if err: return err

            f.write(f"base_time: {effect_entry["base_time"]}\n")
            f.write(f"min: {effect_entry["min"]}\n")
            f.write(f"max: {effect_entry["max"]}\n")
            f.write(f"super_success_amount: {effect_entry["super_success_amount"]}\n")
            multiplier = effect_entry["multiplier"]
            f.write(f"multiplier: {u.hex08(multiplier)}\n")
            f.write(f"multiplier_f32: \"{round(u.f32_bits(multiplier), 2)}f32\"\n")
            f.write("\n")
            f.write(f"code_name: {code_name}\n")
            f.write(f"value: {value}\n")
            if special_status:
                f.write(f"special_status: {special_status}\n")
            else:
                f.write("special_status: null\n")
            if name in cook_effect_localization:
                f.write("localization:\n")
                l10n_data = cook_effect_localization[name]
                for locale, data in l10n_data.items():
                    f.write(f"  {locale}:\n")
                    f.write(f"    name: {json.dumps(data['name'])}\n")
                    f.write(f"    name_feminine: {json.dumps(data['name_feminine'])}\n")
                    f.write(f"    name_masculine: {json.dumps(data['name_masculine'])}\n")
                    f.write(f"    name_neuter: {json.dumps(data['name_neuter'])}\n")
                    f.write(f"    name_plural: {json.dumps(data['name_plural'])}\n")
                    f.write(f"    desc:\n")
                    for desc in data["desc"]:
                        f.write(f"      - {json.dumps(desc)}\n")
                    f.write(f"    elixir_desc:\n")
                    for desc in data["elixir_desc"]:
                        f.write(f"      - {json.dumps(desc)}\n")
            else:
                f.write("localization: null\n")

    print(f"Saved {len(COOK_EFFECTS)} CookEffects")
