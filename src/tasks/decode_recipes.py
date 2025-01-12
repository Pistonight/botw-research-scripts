"""
Decode the recipe file (Cooking/CookData.byml)
"""
import yaml
import util as u
import task as t
import spp

def task():
    inputs = {
        "cook_data_path": "botw/Cooking/CookData.yml",
        "tags_path": "output/tags.yaml",
        "actor_hash_path": "output/actor-hashes.yaml",
        "cook_system_path": "output/cook-system.yaml",
    }

    outputs = {
        "recipe_path": "output/recipes.yaml",
        "recipe_meta_path": "output/recipe-meta.yaml",
    }

    def run(inputs, outputs):
        return decode_recipes(
            inputs["cook_data_path"],
            inputs["actor_hash_path"],
            inputs["tags_path"],
            inputs["cook_system_path"],
            outputs["recipe_path"],
            outputs["recipe_meta_path"],
        )

    return t.task(__file__, inputs, outputs, run)


def decode_recipes(
    cook_data_path: str,
    actor_hash_path: str, 
    tags_hash_path: str,
    cook_system_path: str,
    recipe_path: str,
    recipe_meta_path: str,
) -> str | None:
    data, err = u.fyaml(cook_data_path)
    if err: return err

    actor_hashmap, err = load_hashes(actor_hash_path)
    if err: return err

    tags_hashmap, err = load_hashes(tags_hash_path)
    if err: return err

    system, err = u.fyaml(cook_system_path)
    if err: return err

    # dubious food
    failure_actor, err = u.sfget(system, "failure_actor", str)
    if err: return err

    # The recipe array will be like
    # [...single_recipes, ...recipes]
    # failure_actor_index is the index of dubious food
    # in that array

    failure_actor_index = None
    out_array = []

    single_recipes, err = u.sfget(data, "SingleRecipes", list)
    if err: return err
    single_recipe_count = len(single_recipes)
    progress = spp.printer(single_recipe_count, "Decode SingleRecipes")
    err = decode_recipe(progress, actor_hashmap, tags_hashmap, single_recipes, True, out_array)
    if err: return err
    progress.done()

    recipes, err = u.sfget(data, "Recipes", list)
    if err: return err
    recipe_count = len(recipes)
    progress = spp.printer(recipe_count, "Decode Recipes")
    err = decode_recipe(progress, actor_hashmap, tags_hashmap, recipes, False, out_array)
    if err: return err
    progress.done()

    total = len(out_array)
    err = u.ensure(total == single_recipe_count + recipe_count, f"expected {single_recipe_count + recipe_count} recipes, got {total}")
    if err: return err

    for (i, recipe) in enumerate(out_array):
        if recipe["recipe"] == failure_actor:
            if failure_actor_index is not None:
                return "found multiple dubious food recipes"
            failure_actor_index = i
    if failure_actor_index is None:
        return "failed to find dubious food recipe"

    recipe_tags = set()
    recipe_actors = set()
    recipe_outputs = set()
    for recipe in out_array:
        recipe_outputs.add(recipe["recipe"])
        for tgroup in recipe["tags"]:
            if isinstance(tgroup, list):
                for tag in tgroup:
                    err = u.ensure(isinstance(tag, str), "expected tag to be string")
                    if err: return err
                    recipe_tags.add(tag)
            else:
                err = u.ensure(isinstance(tgroup, str), "expected tag group to be either list or string")
                if err: return err
                recipe_tags.add(tgroup)
        for agroup in recipe["actors"]:
            if isinstance(agroup, list):
                for actor in agroup:
                    err = u.ensure(isinstance(actor, str), "expected actor to be string")
                    if err: return err
                    recipe_actors.add(actor)
            else:
                err = u.ensure(isinstance(agroup, str), "expected actor group to be either list or string")
                if err: return err
                recipe_actors.add(agroup)


    meta = {
        "failure_actor_index": failure_actor_index,
        "single_recipe_count": single_recipe_count,
        "recipe_count": recipe_count,
        "total_count": total,
        "tags_used_for_matching": sorted(recipe_tags),
        "actors_used_for_matching": sorted(recipe_actors),
        "output_actors": sorted(recipe_outputs),
    }

    with u.fopenw(recipe_meta_path) as f:
        yaml.dump(meta, f)

    with u.fopenw(recipe_path) as f:
        yaml.dump(out_array, f)


def decode_recipe(
    progress: spp._Printer,
    actor_hashmap: dict[int, str],
    tags_hashmap: dict,
    data: list,
    is_single: bool,
    out: list,
) -> str | None:
    for (i, recipe) in enumerate(data):
        name, err = u.sfget(recipe, "Recipe", int)
        if err: return err
        name, err = decode_object(name, actor_hashmap)
        if err: return err

        progress.print(i, name)

        actors, err = u.sfgetopt(recipe, "Actors", list)
        if err: return err
        if actors:
            actors, err = decode_object(actors, actor_hashmap)
            if err: return err
        else:
            actors = []

        tags, err = u.sfgetopt(recipe, "Tags", list)
        if err: return err
        if tags:
            tags, err = decode_object(tags, tags_hashmap)
            if err: return err
        else:
            tags = []

        hb, err = u.sfgetopt(recipe, "HB", int)
        if err: return err
        if not hb:
            hb = 0
        if is_single:
            num, err = u.sfget(recipe, "Num", int)
            if err: return err
            if num != 1: return f"{name}: expected Num to be 1 in single recipe, got {num}"
        out.append({
            "recipe": name,
            "actors": actors,
            "tags": tags,
            "heart_bonus": hb,
        })
    return None

            
def decode_object[T](obj: T, hashmap: dict[int, str]) -> tuple[T, str | None]:
    if isinstance(obj, list):
        out = []
        for item in obj:
            decoded, err = decode_object(item, hashmap)
            if err: return None, err # type: ignore
            out.append(decoded)
        return out, None # type: ignore
    err = u.ensure(isinstance(obj, int), "expected hash object in recipe to be either list or int")
    if err: return None, err # type: ignore
    if obj not in hashmap:
        return None, f"unknown hash: {u.hex08(obj)}" # type: ignore
    return hashmap[obj], None

def load_hashes(hash_path: str) -> tuple[dict[int, str], str | None]:
    hashmap = {}
    data, err = u.fyaml(hash_path)
    if err: return {}, err

    for hash_str, actor in data.items():
        try:
            hash = int(hash_str, 16)
        except Exception as e:
            return {}, f"failed to parse hash: {hash_str}: {e}"
        hashmap[hash] = actor
    return hashmap, None
