"""
Generate CRC32 hashes for actor names
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
        "hash_save_path": "output/actor-hashes.yaml",
    }

    def run(inputs, outputs):
        return hash_actors(inputs["actor_dir"], outputs["hash_save_path"])

    return t.task(__file__, inputs, outputs, run)

def hash_actors(actor_dir: str, save_path: str) -> str | None:
    names = set()

    for (i, actor_file) in enumerate(os.listdir(actor_dir)):
        err = u.ensure(actor_file.endswith(".yaml"), f"Actor file must be a yaml file: {actor_file}")
        if err: return err
        actor_name = actor_file[:-5]
        names.add(actor_name)

    hashs = set()

    progress = spp.printer(len(names), "Hash actor names")
    progress.done()


    with u.fopenw(save_path) as f:
        for i, name in enumerate(sorted(names)):
            progress.print(i, name)
            hash_num = u.crc32(name)
            hash = u.hex08(hash_num)
            if hash_num in hashs:
                return f"hash collision: {name} {u.hex08(hash_num)}"
            hashs.add(hash_num)
            f.write(f"\"{hash}\": {name}\n")

    print(f"Saved {len(names)} names to {u.relpath(save_path)}")
    return None
