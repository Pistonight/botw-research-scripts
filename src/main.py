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

    u.fatal(mgr.finish())
