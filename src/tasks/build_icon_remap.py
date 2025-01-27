"""
Build the actor -> icon actor dictionary for mapping actors with the same icon
"""

import os
import util as u
import task as t
import yaml
import spp

def task():
    inputs = {
        "actor_dir": "output/Actor",
    }

    outputs = {
        "output_path": "output/actor-icon-remap.yaml",
    }

    def run(inputs, outputs):
        return build_icon_remap(
            inputs["actor_dir"],
            outputs["output_path"],
        )

    return t.task(__file__, inputs, outputs, run)

# names for actors that don't have one
MANUAL_NAME = {
    "Weapon_Sword_071": "Master Sword",
    "Weapon_Sword_072": "Master Sword",
}

# Actors to ignore if they have this name
IGNORE_NAME = set([
    # Not Items (don't have icon anyway)
    "Korok",
    "Traveler",
    "???",
    "Remote Bomb",
    "Remote Bomb +",
    "Monument Shard",
    "Finley",
    "Great Fairy Fountain",

    # Manually duplicated
    "Thunder Helm",

    # Two distinct items with same name
    "Light Arrows",
])


def build_icon_remap(actor_dir: str, output_path: str) -> str | None:
    # Multiple actors have this name, so we need to pick one manually
    manual_resolution = {
        "Snow Boots": "Armor_141_Lower",
        "Master Sword": "Weapon_Sword_070",
        "Sheikah Slate": "Obj_DRStone_Get",
    }

    actor_files = [ os.path.join(actor_dir, x) for x in os.listdir(actor_dir)]

    name_to_actor_and_icon = {}
    progress = spp.printer(len(actor_files), "Load icon actor info")
    with u.pool() as pool:
        for (i, result) in enumerate(pool.imap_unordered(process_actor, actor_files)):
            progress.update(i)

            result, err = result
            if err: return "failed: " + str(err)

            if not result:
                continue

            name, actor_name, icon_actor_name = result
            if name in name_to_actor_and_icon:
                data = name_to_actor_and_icon[name]
                data["actors"].append(actor_name)
                data["icons"].add(icon_actor_name)
            else:
                data = {
                    "actors": [actor_name],
                    "icons": set([icon_actor_name]),
                }
                name_to_actor_and_icon[name] = data
    progress.done()
    # actor name -> icon actor name, if not the same
    resolution = {}

    progress = spp.printer(len(name_to_actor_and_icon), "Resolve icon actor")

    for (i, name) in enumerate(name_to_actor_and_icon):
        progress.print(i, name)
        data = name_to_actor_and_icon[name]
        actors = data["actors"]
        # if only one actor has this name, skip
        if len(actors) <= 1:
            continue
        icons = data["icons"]
        if len(icons) > 1:
            # more than one icon, needs manual resolution
            if name not in manual_resolution:
                print(f"actors: {actors}")
                print(f"icons: {icons}")
                return f"Manual resolution needed for {name}"
            icon = manual_resolution[name]
            if icon not in icons:
                return f"In manual resolution for {name}: Icon {icon} not in {icons}"
            for actor in actors:
                if actor != icon:
                    # print(f"{actor} -> {icon}")
                    resolution[actor] = icon
        else:
            icon = next(iter(icons))
            # only one icon, resolve to it
            for actor in actors:
                if actor != icon:
                    # print(f"{actor} -> {icon}")
                    resolution[actor] = icon
    print(f"Remapped {len(resolution)} actors")
    progress.done()

    with u.fopenw(output_path) as f:
        yaml.dump(resolution, f, sort_keys=True)

    return None

def process_actor(actor_path: str) -> tuple[tuple[str, str, str] | None, str | None]:
    """
        Return (localized_name, actor_name, icon_actor_name)
        Return None if actor doesn't have translation
    """
    actor, err = u.fyaml(actor_path)
    if err: return None, err

    actor_name = actor["actor"]

    # load the localized name
    if actor_name in MANUAL_NAME:
        name = MANUAL_NAME[actor_name]
    else:
        if not actor["localization"]:
            return None, None
        strings = actor["localization"]["en-US"]
        if not strings["name"]:
            return None, None
        name = strings["name"]["text"]
        if name in IGNORE_NAME:
            return None, None

    # find the icon actor from gparam
    icon_actor = actor_name
    if actor["gparamlist"]:
        if "itemUseIconActorName" in actor["gparamlist"]:
            icon_actor = actor["gparamlist"]["itemUseIconActorName"]

    return (name, actor_name, icon_actor), None
