"""
Build maps for Actor -> Recipe and Tag -> Recipe
that can be used to improve recipe search performance
"""

import os
import spp
import util as u
import task as t

def task():
    inputs = {
        "actor_dir": "output/Actor",
        "recipes_path": "output/recipes.yaml",
        "recipe_meta_path": "output/recipe-meta.yaml",
    }

    outputs = {
        "actor_output": "output/recipe-actor-index.yaml",
        "tag_output": "output/recipe-tag-index.yaml",
    }

    def run(inputs, outputs):
        return build_recipe_index(
            inputs["actor_dir"],
            inputs["recipes_path"],
            inputs["recipe_meta_path"],
            outputs["actor_output"],
            outputs["tag_output"],
        )

    return t.task(__file__, inputs, outputs, run)

def build_recipe_index(
    actor_dir: str,
    recipes_path: str,
    recipe_meta_path: str,
    actors_save_path: str,
    tags_save_path: str
) -> str | None:
    recipes, err = u.fyaml(recipes_path)
    if err: return err

    recipe_meta, err = u.fyaml(recipe_meta_path)
    if err: return err

    # only check non-single recipes
    recipes = recipes[recipe_meta["single_recipe_count"]:]

    actors_to_matchable_recipe_idxs: dict[str, set[int]] = {}
    tags_to_matchable_recipe_idxs: dict[str, set[int]] = {}

    def to_list(x):
        if not isinstance(x, list):
            return [x]
        return x

    progress = spp.printer(len(recipes), "Build recipe index")

    for (i, recipe) in enumerate(recipes):
        progress.print(i, recipe["recipe"])
        for a in recipe["actors"]:
            for actor in to_list(a):
                if actor not in actors_to_matchable_recipe_idxs:
                    actors_to_matchable_recipe_idxs[actor] = set([i])
                else:
                    actors_to_matchable_recipe_idxs[actor].add(i)

        for t in recipe["tags"]:
            for tag in to_list(t):
                if tag not in tags_to_matchable_recipe_idxs:
                    tags_to_matchable_recipe_idxs[tag] = set([i])
                else:
                    tags_to_matchable_recipe_idxs[tag].add(i)

    progress.done()
    files = os.listdir(actor_dir)
    progress = spp.printer(len(files), "Expand tags to actors")

    for (i, file) in enumerate(files):
        progress.print(i, file)
        actor_data, err = u.fyaml(os.path.join(actor_dir, file))
        if err: return err

        actor_name = actor_data["actor"]
        tags = actor_data["tags"]
        for tag in tags:
            if tag not in tags_to_matchable_recipe_idxs:
                continue
            for idx in tags_to_matchable_recipe_idxs[tag]:
                if actor_name not in actors_to_matchable_recipe_idxs:
                    actors_to_matchable_recipe_idxs[actor_name] = set([idx])
                else:
                    actors_to_matchable_recipe_idxs[actor_name].add(idx)
    progress.done()

    actors_output, err = convert_to_recipe_set(len(recipes), actors_to_matchable_recipe_idxs)
    if err: return err

    with u.fopenw(actors_save_path) as f:
        f.write("# See build_recipe_index.py for the bit encoding\n\n")
        for key in actors_output:
            a1, a2 = actors_output[key]
            f.write(f"{key:<20}: [0x{a1:016x}, 0x{a2:016x}]\n")

    tags_output, err = convert_to_recipe_set(len(recipes), tags_to_matchable_recipe_idxs)
    if err: return err
    with u.fopenw(tags_save_path) as f:
        f.write("# See build_recipe_index.py for the bit encoding\n\n")
        for key in tags_output:
            a1, a2 = tags_output[key]
            f.write(f"{key:<20}: [0x{a1:016x}, 0x{a2:016x}]\n")

def convert_to_recipe_set(max: int, data: dict[str, set[int]]) -> tuple[dict[str, tuple[int, int]], str | None]:
    if max > 64*2:
        return None, "Too many recipes to index" # type: ignore

    output = {}
    for key in data:
        s = data[key]
        
        a1 = 0
        for i in range(0, 64):
            if i in s:
                a1 = (a1 | (1 << i))
        a2 = 0
        for i in range(64, max):
            if i in s:
                a2 = (a2 | (1 << (i-64)))

        output[key] = (a1, a2)

    return output, None


