"""
Build the armor upgrade data
"""

import util as u
import task as t
import yaml
import spp

def task():
    inputs = {
        "actor_icon_remap_path": "output/actor-icon-remap.yaml",
    }

    outputs = {
        "output_path": "output/armor-upgrades.yaml",
    }

    def run(inputs, outputs):
        return build_armor_upgrade(
            inputs["actor_icon_remap_path"],
            outputs["output_path"],
        )

    return t.task(__file__, inputs, outputs, run)


def build_armor_upgrade(actor_icon_remap_path: str, output_path: str) -> str | None:
    icon_remap, err = u.fyaml(actor_icon_remap_path)
    if err: return err

    armor_groups, err = icon_remap_to_armor_upgrade_data(icon_remap)
    if err: return err

    with u.fopenw(output_path) as f:
        for group in armor_groups:
            f.write(f"- [{', '.join(group)}]\n")


def icon_remap_to_armor_upgrade_data(icon_remap: dict[str, str]) -> tuple[list[str], str | None]:
    """Get armor upgrade map from actor icon resolution"""

    progress = spp.printer(len(icon_remap), "Build armor upgrade data")

    armor_groups = []
    def add_group(actor_1, actor_2):
        for group in armor_groups:
            if actor_1 in group or actor_2 in group:
                group.add(actor_1)
                group.add(actor_2)
                return
        armor_groups.append(set([actor_1, actor_2]))
    for i, (actor_1, actor_2) in enumerate(icon_remap.items()):
        progress.print(i, f"{actor_1} and {actor_2}")
        if actor_1.startswith("Armor_") and actor_2.startswith("Armor_"):
            add_group(actor_1, actor_2)

    progress.done()

    filtered_groups = []
    to_remove = [
        # snow boots that's not upgradable (borrowed)
        # code should hardcode checking for this
        "Armor_140_Lower", 
    ]
    for group in armor_groups:
        for remove in to_remove:
            if remove in group:
                group.remove(remove)
        if len(group) == 1:
            continue
        if len(group) == 5:
            edited_group = []
            for actor in sorted(group):
                if not actor.startswith("Armor_"):
                    raise Exception(f"Unexpected actor: {actor}")
                edited_group.append(actor[6:])
            filtered_groups.append(edited_group)
            continue
        if len(group) == 2:
            # ignore the sheika slate group
            if "Obj_DRStone_Get" in group:
                continue
        return [], f"Unexpected group: {group}"

    filtered_groups.sort(key=lambda x: x[0])

    return filtered_groups, None
