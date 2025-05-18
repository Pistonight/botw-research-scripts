import os
import util as u
import task as t

if __name__ == "__main__":
    output = u.output(".")
    if not os.path.exists(output):
        os.makedirs(output)

    mgr = t.mgr()
    from tasks import link_actors
    u.fatal(mgr.add(link_actors.task()))
    from tasks import list_tags
    u.fatal(mgr.add(list_tags.task()))
    from tasks import link_effects
    u.fatal(mgr.add(link_effects.task()))
    from tasks import decode_cook_system
    u.fatal(mgr.add(decode_cook_system.task()))
    from tasks import hash_actors
    u.fatal(mgr.add(hash_actors.task()))
    from tasks import decode_recipes
    u.fatal(mgr.add(decode_recipes.task()))
    from tasks import build_recipe_groups
    u.fatal(mgr.add(build_recipe_groups.task()))
    from tasks import build_recipe_index
    u.fatal(mgr.add(build_recipe_index.task()))
    from tasks import build_icon_remap
    u.fatal(mgr.add(build_icon_remap.task()))
    from tasks import build_armor_upgrade
    u.fatal(mgr.add(build_armor_upgrade.task()))
    from tasks import list_gamedata
    u.fatal(mgr.add(list_gamedata.task()))

    u.fatal(mgr.finish())
