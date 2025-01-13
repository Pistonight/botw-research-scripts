"""
Group actors based their effect when used in a recipe
"""

import os
import util as u
import task as t
from typing import Any
import spp

def task():
    inputs = {
        "actor_dir": "output/Actor",
        "recipe_meta_path": "output/recipe-meta.yaml",
    }

    outputs = {
        "recipe_groups_path": "output/recipe-groups.yaml",
    }

    def run(inputs, outputs):
        return build_recipe_groups(
            inputs["actor_dir"],
            inputs["recipe_meta_path"],
            outputs["recipe_groups_path"]
        )

    return t.task(__file__, inputs, outputs, run)

# Keys to compare to check if two actors are the same
# If any of these keys are different, the actors are considered different
COMPARE_KEYS = [
    "cookSpiceBoostEffectiveTime",
    "cookSpiceBoostMaxHeartLevel",
    "cookSpiceBoostStaminaLevel",
    "cookSpiceBoostSuccessRate",
    "cureItemEffectLevel",
    "cureItemEffectType",
    "cureItemEffectiveTime",
    "cureItemHitPointRecover",
    "itemBuyingPrice",
    "itemSellingPrice",
]

# Keys to determine if an actor cannot be grouped (itself is its own group)
# If any of these keys are present, the actor cannot be groupped
NON_GROUP_KEYS = set([
    "cookSpiceBoostHitPointRecover",
])

# Tags referenced in the cooking code
EXTRA_TAGS = [
    "CookLowPrice",
    "CookEnemy",
    "CookSpice"
]

class Group:
    actors: list[str]
    gparamlist: dict[str, Any] # trimmed version with only the COMPARE_KEYS
    tags: set[str] # trimmed version with only the important tags
    non_group: bool

    def __init__(self, actor: str, gparamlist: dict[str, Any], tags: set[str]):
        self.actors = [actor]
        self.gparamlist = gparamlist
        self.tags = tags
        self.non_group = False

def build_recipe_groups(
    actor_dir: str,
    recipe_meta_path: str,
    save_path: str
) -> str | None:
    recipe_meta, err = u.fyaml(recipe_meta_path)
    if err: return err

    # Actors that appear in the recipes must be its own group
    non_group_actors, err = u.sfget(recipe_meta, "actors_used_for_matching", list)
    if err: return err
    non_group_actors = set(non_group_actors)

    # If an actor has any of these tags, it cannot be grouped
    important_tags, err = u.sfget(recipe_meta, "tags_used_for_matching", list)
    if err: return err
    important_tags = set(important_tags + EXTRA_TAGS)

    # These output actors won't be grouped
    output_actors, err = u.sfget(recipe_meta, "output_actors", list)
    if err: return err
    output_actors = set(output_actors)

    # As a hack right now, also exclude monster extract
    output_actors.add("Item_Material_08")

    files = [ (os.path.join(actor_dir, x), non_group_actors, important_tags) for x in os.listdir(actor_dir) if x.endswith(".yaml") and x[:-5] not in output_actors ]
    progress = spp.printer(len(files), "Load actors for grouping")

    errors = []

    groups: list[Group] = []
    # (actor_name, gparamlist, tags)
    to_group: list[tuple[str, dict[str, Any], set[str]]] = []

    with u.pool() as pool:
        for (i, (actor_name, (status, data), error)) in enumerate(pool.imap(process_actor_shim, files)):
            progress.print(i, actor_name)
            if error:
                errors.append(error)
                continue
            if status == "skip":
                continue
            if status == "non-group":
                _group = Group(actor_name, {}, set())
                _group.non_group = True
                groups.append(_group)
                continue
            err = u.ensure(data is not None, "data is None")
            if err:
                errors.append(err)
                continue
            gparamlist, tags = data # type: ignore bro I literally checked for None
            to_group.append((actor_name, gparamlist, tags))
    progress.done()

    err = u.check_errors(errors)
    if err: return err

    progress = spp.printer(len(to_group), "Group actors")

    for (i, (actor_name, gparamlist, tags)) in enumerate(to_group):
        progress.print(i, actor_name)
        found = False
        for group in groups:
            if group.non_group:
                continue
            if group.gparamlist == gparamlist and group.tags == tags:
                group.actors.append(actor_name)
                found = True
                break
        if not found:
            groups.append(Group(actor_name, gparamlist, tags))
    progress.done()

    # Write the groups
    with u.fopenw(save_path) as f:
        for group in groups:
            group.actors.sort()
            f.write(f"- {group.actors}\n")

    print(f"Saved {len(groups)} groups to {u.relpath(save_path)}")

    return None


def process_actor_shim(args):
    return process_actor(*args)
def process_actor(
    actor_path: str, 
    non_group_actors: set[str], 
    important_tags: set[str]
) -> tuple[
    str, # actor_name
    tuple[str, tuple[dict[str, Any], set[str]] | None], # status and data
    str | None # error
]:
    """
        Process the parameter of the actor and return information for grouping

        Returns: actor, (status, data), error
          - status is:
            - "skip" if the actor should be skipped, (not considered at all)
            - "non-group" if the actor should be its own group
            - "group" if the actor should be grouped
          If status is "group" then data is a tuple:
            - its gparamlist data with the keys in COMPARE_KEYS
            - its tags as a subset of important_tags

    """
    def mkerr(e):
        return "", ("", None), e
    actor_data, err = u.fyaml(actor_path)
    if err: return mkerr(err)
    actor_name, err = u.sfget(actor_data, "actor", str)
    if err: return mkerr(err)

    profile, err = u.sfgetnullable(actor_data, "profile", str)
    if err: return mkerr(f"failed to load profile for {actor_name}: {err}")
    if profile is None:
        return actor_name, ("skip", None), None

    # Weapon/Bow/Shield, Armor and Arrow are not holdable
    # Skip them
    if profile in (
        "WeaponShield", "WeaponSpear", "WeaponSmallSword", "WeaponLargeSword",
        "WeaponBow", "Bullet",
        "ArmorLower", "ArmorUpper", "ArmorHead"
    ):
        return actor_name, ("skip", None), None

    if actor_name in non_group_actors:
        return actor_name, ("non-group", None), None

    # Check the gparamlist
    gparamlist, err = u.sfget(actor_data, "gparamlist", dict)
    if err: return mkerr(err)

    for key in gparamlist:
        if key in NON_GROUP_KEYS:
            return actor_name, ("non-group", None), None

    tags, err = u.sfget(actor_data, "tags", list)
    if err: return mkerr(err)
    trimmed_tags = set()
    for tag in tags:
        if tag in important_tags:
            trimmed_tags.add(tag)

    trimmed_gparamlist = {}
    for key in COMPARE_KEYS:
        if key in gparamlist:
            trimmed_gparamlist[key] = gparamlist[key]

    return actor_name, ("group", (trimmed_gparamlist, trimmed_tags)), None
