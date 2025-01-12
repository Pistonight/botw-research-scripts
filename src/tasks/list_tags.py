"""
List all tags ActorLinks can have
"""
import os
import util as u
import task as t
import spp

def task():
    inputs = {
        "actor_dir": "output/Actor",
    }

    outputs = {
        "tags_save_path": "output/tags.yaml",
    }

    def run(inputs, outputs):
        return list_tags(inputs["actor_dir"], outputs["tags_save_path"])

    return t.task(__file__, inputs, outputs, run)

def list_tags(actor_dir: str, tags_save_path: str) -> str | None:
    files = os.listdir(actor_dir)
    progress = spp.printer(len(files), "List tags")
    tags = set()

    # tags not on any actor but used in some system (like cooking)
    tags.update([
        "CookVegetable"
    ])

    errors = []

    with u.pool() as pool:
        for (i, ((actor_name, actor_tags), err)) in enumerate(pool.imap_unordered(get_tags_from_actor, [os.path.join(actor_dir, file) for file in files])):
            if err:
                errors.append(err)
                progress.update(i)
                continue
            tags.update(actor_tags)
            progress.print(i, actor_name)
    progress.done()

    err = u.check_errors(errors)
    if err: return err

    hashs = set()

    with u.fopenw(tags_save_path) as f:
        for tag in sorted(tags):
            hash_num = u.crc32(tag)
            hash = u.hex08(hash_num)
            if hash_num in hashs:
                return f"hash collision: {tag} {u.hex08(hash_num)}"
            hashs.add(hash_num)
            f.write(f"\"{hash}\": {tag}\n")

    print(f"Saved {len(tags)} tags to {u.relpath(tags_save_path)}")
    return None


def get_tags_from_actor(actor_file) -> tuple[tuple[str, list[str]], str | None]:
    """ Get all tags from an actor file """
    actor, err = u.fyaml(actor_file)
    if err: return ("", []), err
    return (actor["actor"], actor["tags"]), None
