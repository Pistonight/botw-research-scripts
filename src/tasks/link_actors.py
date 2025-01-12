"""
Link an actor (ActorLink) with its GParams and localization
"""
import os
import yaml
import json
import shutil
from dataclasses import dataclass
from typing import Any
import util as u
import task as t
import msyt
import spp

def task():
    inputs = {
        "actor_link_dir": "botw/Actor/ActorLink",
        "dummy_path": "botw/Actor/GeneralParamList/Dummy.gparamlist.yml",
        "gparam_dir": "botw/Actor/GeneralParamList",
        "messages": "botw/Message",
    }

    outputs = {
        "actor_output_dir": "output/Actor",
        "gpk_save_path": "output/gpks.yaml",
    }

    def run(inputs, outputs):
        gparamkeys, err = load_gparam_keys(inputs["dummy_path"], outputs["gpk_save_path"])
        if err: return err
        actors, err = load_actor_links(inputs["actor_link_dir"])
        if err: return err
        gparamlists, err = load_gparamlist_files(gparamkeys, inputs["gparam_dir"])
        if err: return err
        localization, err = load_actor_localization()
        if err: return err
        err = save_output(actors, gparamlists, localization, outputs["actor_output_dir"])
        if err: return err

        return None

    return t.task(__file__, inputs, outputs, run)





class ActorLink:
    actor: str
    name_jpn: str
    tags: list[str]
    model: str = ""
    gparamlist: str = ""
    profile: str = ""

def load_actor_links(actor_link_dir: str) -> tuple[dict[str, ActorLink], str | None]:
    files = os.listdir(actor_link_dir)
    progress = spp.printer(len(files), "Linking Actors")

    actor_links = {}
    errors = []

    with u.pool() as pool:
        for i, (actor, err) in enumerate(pool.imap_unordered(load_actor_link, [os.path.join(actor_link_dir, f) for f in files])):
            if err:
                errors.append(err)
                continue
            if not actor:
                progress.update(i)
                errors.append("load_actor_link returned None")
                continue
            actor_links[actor.actor] = actor
            progress.print(i, actor.actor)
    progress.done()

    err = u.check_errors(errors)
    if err: return {}, err

    return actor_links, None

def load_actor_link(path: str) -> tuple[ActorLink | None, str | None]:
    err = u.ensure(path.endswith(".yml"), "ActorLink file must end in .yml")
    if err: return None, err
    actor_name = os.path.basename(path)[:-4]

    data, err = u.fyaml(path)
    if err: return None, err

    actor = ActorLink()
    actor.actor = actor_name.strip()
    actor.tags = []

    param_root, err = u.sfget(data, "param_root", dict)
    if err: return None, err
    objects, err = u.sfget(param_root, "objects", dict)
    if err: return None, err
    link_targets, err = u.sfget(objects, "LinkTarget", dict)
    if err: return None, err

    name_jpn, err = u.sfget(link_targets, "ActorNameJpn", str)
    if err: return None, err
    actor.name_jpn = name_jpn

    model, err = u.sfgetopt(link_targets, "ModelUser", str)
    if err: return None, err
    if model:
        if model == "Dummy":
            model = ""
        actor.model = model.strip()

    gparamlist, err = u.sfgetopt(link_targets, "GParamUser", str)
    if err: return None, err
    if gparamlist:
        if gparamlist == "Dummy":
            gparamlist = ""
        actor.gparamlist = gparamlist.strip()

    profile, err = u.sfgetopt(link_targets, "ProfileUser", str)
    if err: return None, err
    if profile: 
        if profile == "Dummy":
            profile = ""
        actor.profile = profile.strip()

    tags, err = u.sfgetopt(objects, "Tags", dict)
    if err: return None, err
    if tags:
        for i in range(0, 99): # at most 20 something tags
            tag_name = f"Tag{i}"
            tag, err = u.sfgetopt(tags, tag_name, str)
            if err: return None, err
            if not tag:
                break
            actor.tags.append(tag.strip())
        err = u.ensure(len(actor.tags) == len(set(actor.tags)), f"{actor_name}: ActorLink tags must be unique, but got: {actor.tags}")
        if err: return None, err

    return actor, None

@dataclass
class Gpk:
    """A key for GParamList"""
    name: str
    default: str | int | float | bool | None

def load_gparam_keys(dummy_path: str, gpk_save_path: str) -> tuple[list[Gpk], str | None]:
    """Load default GParam values from Dummy and save them to a YAML file"""
    keys = []
    with u.fopenr(dummy_path) as f:
        # not using YAML parser for the whole thing to preserve key order
        current_key_prefix: str = ""
        current_table: list[str] = []
        for line in f:
            if not line.startswith("    "):
                continue
            line = line[4:]
            if not line.startswith(" "):
                if current_table:
                    # table end
                    data = yaml.load("\n".join(current_table), yaml.FullLoader)
                    err = u.ensure(data and isinstance(data, dict) and len(data) == 1, "Table must not be empty")
                    if err: return [], err
                    current_key= list(data.keys())[0]
                    current_key_prefix = current_key[0].lower() + current_key[1:]
                    data = data[current_key]
                    for key in sorted(data.keys()):
                        keys.append(Gpk(current_key_prefix + key, data[key]))

                current_table = []
                current_key_prefix = ""

                line = line.strip()
                if line.endswith("!obj") or line.endswith(":"):
                    # line is just table name
                    key = line.split(":")[0].strip()
                    current_key_prefix = key[0].lower() + key[1:]
                else:
                    # table inline (need to parse whole table together)
                    current_table = [line]
                continue
            if current_table:
                current_table.append(line)
                continue
            line = line.strip()
            data = yaml.load(line, yaml.FullLoader)
            err = u.ensure(data and isinstance(data, dict) and len(data) == 1, "Data must not be empty")
            if err: return [], err
            key = list(data.keys())[0]
            keys.append(Gpk(current_key_prefix+key, data[key]))

    with u.fopenw(gpk_save_path) as f:
        for key in keys:
            data = yaml.dump({key.name: key.default})
            f.write(data)
    print(f"Saved {len(keys)} Gpks to {u.relpath(gpk_save_path)}")
    return keys, None

def load_gparamlist_files(keys: list[Gpk], gparam_dir: str) -> tuple[dict[str, list[tuple[str, object]]], str | None]:
    """
    Load GParamLists and return GParamUser -> GParams

    Only values different from the default are stored
    """
    files = os.listdir(gparam_dir)
    gparamlist = {}
    progress = spp.printer(len(files), "Loading GParamLists")

    errors = []

    with u.pool() as pool:
        for i, ((gparamlist_name, gparam_entries), err) in enumerate(
            pool.imap_unordered(load_gparamlist_file_shim, [(keys, os.path.join(gparam_dir, f)) for f in files])):
            if err:
                progress.update(i)
                errors.append(err)
                continue
            if not gparamlist_name:
                progress.update(i)
                errors.append("load_gparamlist_file returned empty name")
                continue
            gparamlist[gparamlist_name] = gparam_entries
            progress.print(i, gparamlist_name)
    progress.done()

    err = u.check_errors(errors)
    if err: return {}, err

    return gparamlist, None

def load_gparamlist_file_shim(args) -> tuple[
    tuple[ str, list[tuple[str, Any]] ]
    , str | None]:
    return load_gparamlist_file(*args)
def load_gparamlist_file(keys: list[Gpk], gparam_path: str) -> tuple[tuple[str, list[tuple[str, Any]]], str | None]:
    err = u.ensure(gparam_path.endswith(".gparamlist.yml"), "GParamList file must end in .yml")
    if err: return ("", []), err
    gparamlist_name = os.path.basename(gparam_path)[:-15]

    data, err = u.fyaml(gparam_path)
    if err: return ("", []), err
    param_root, err = u.sfget(data, "param_root", dict)
    if err: return ("", []), err
    objects, err = u.sfget(param_root, "objects", dict)
    if err: return ("", []), err

    objects = flatten_gpl(objects)

    parsed = []
    for key in keys:
        name = key.name
        if name not in objects:
            continue
        value = objects[name]
        del objects[name]
        if value == key.default:
            continue
        if value is None:
            return ("", []), f"Key {name} in {gparamlist_name} is None"
        parsed.append((name, value))

    unknown_keys = set(objects.keys())
    if unknown_keys:
        return ("", []), f"Unknown keys in {gparamlist_name}: {unknown_keys}"

    return (gparamlist_name, parsed), None


def flatten_gpl(obj):
    """Flatten a GeneralParamList object"""
    out = {}
    for key in obj:
        lower = key[0].lower() + key[1:]
        for subkey in obj[key]:
            out[lower + subkey] = obj[key][subkey]
    return out

# actor localization stuff
@dataclass
class LocalizationStrings:
    name: str = ""
    name_attr: str = ""
    desc: str = ""
    album_desc: str = ""

@dataclass
class LocalizationEntry:
    profile: str
    strings: dict[str, LocalizationStrings]

def load_actor_localization() -> tuple[dict[str, LocalizationEntry], str | None]:
    entries = {}
    for locale, locale_nin in msyt.locale_map.items():
        err = load_l10n_for_locale(locale, locale_nin, entries)
        if err: return {}, err
    return entries, None

def load_l10n_for_locale(locale: str, locale_nin: str, entries: dict[str, LocalizationEntry]) -> str | None:
    localization_path = u.botw("Message", f"Msg_{locale_nin}.product.sarc", "ActorType")
    progress = spp.printer(len(entries), f"Loading {locale} localization")
    count = 0

    for file in os.listdir(localization_path):
        err = u.ensure(file.endswith(".msyt"), "Localization file must end in .msyt")
        if err: return err
        profile = file[:-5]
        data, err = u.fyaml(os.path.join(localization_path, file))
        if err: return err
        next_count, err = load_l10n_for_locale_profile(count, progress, locale, profile, data, entries)
        if err: return err
        count += next_count
    progress.done()

def load_l10n_for_locale_profile(
        i: int,
        progress: spp._Printer,
        locale: str, 
        profile: str, 
        data, 
        entries: dict[str, LocalizationEntry]) -> tuple[int, str | None]:
    """Load actor localization for a specific locale and profile"""
    entries_data, err = u.sfget(data, "entries", dict)
    if err: 
        return 0, f"failed to load {locale}/ActorType/{profile}: {err}"
    actor_names = set()
    for entry_name, entry_data in entries_data.items():
        actor_name = None
        if entry_name.endswith("_Name"):
            actor_name = entry_name[:-5]
            text, attr, err = msyt.parse_localization(entry_data, True )
            if err: return 0, f"{profile} {actor_name}: {err}"
            strings = ensure_l10n_entry(entries, profile, actor_name, locale)
            strings.name = text
            strings.name_attr = attr
        elif entry_name.endswith("_Desc"):
            actor_name = entry_name[:-5]
            text, attr, err = msyt.parse_localization(entry_data, False )
            if err: return 0, f"{profile} {actor_name}: {err}"
            strings = ensure_l10n_entry(entries, profile, actor_name, locale)
            strings.desc = text
        elif entry_name.endswith("_PictureBook"):
            actor_name = entry_name[:-13]
            text, attr, err = msyt.parse_localization(entry_data, False )
            if err: return 0, f"{profile} {actor_name}: {err}"
            strings = ensure_l10n_entry(entries, profile, actor_name, locale)
            strings.album_desc = text

        if actor_name:
            actor_names.add(actor_name)
            progress.print(i + len(actor_names), actor_name)
    return len(actor_names), None

def ensure_l10n_entry(entries: dict[str, LocalizationEntry], profile: str, actor: str, locale: str) -> LocalizationStrings:
    if actor not in entries:
        strings = {}
        for l in msyt.locale_map:
            strings[l] = LocalizationStrings()
        entries[actor] = LocalizationEntry(profile, strings)
    entry = entries[actor]
    return entry.strings[locale]

def save_output(actors, gparamlists, localization, actor_output_dir) -> str | None:
    if os.path.exists(actor_output_dir):
        shutil.rmtree(actor_output_dir)
    os.makedirs(actor_output_dir)

    progress = spp.printer(len(actors), "Saving Actor files")

    for (i, (actor_name, actor)) in enumerate(actors.items()):
        progress.print(i, actor_name)
        with u.fopenw(os.path.join(actor_output_dir, f"{actor_name}.yaml")) as f:
            f.write(f"actor: {actor_name}\n")
            f.write(f"name_jpn: {actor.name_jpn}\n")
            if actor.tags:
                f.write("tags:\n")
                for tag in actor.tags:
                    f.write(f"  - {tag}\n")
            else:
                f.write("tags: []\n")
            if actor.model:
                f.write(f"model: {actor.model}\n")
            else:
                f.write("model: null\n")
            if actor.gparamlist:
                f.write(f"gparamlist:\n")
                f.write(f"  user: {actor.gparamlist}\n")
                f.write(f"  # ---\n")
                for key, value in gparamlists[actor.gparamlist]:
                    if isinstance(value, list):
                        data = json.dumps(value)
                        f.write(f"  {key}: {data}\n")
                    else:
                        data = yaml.dump({key: value})
                        f.write(f"  {data}")
                        if not data.endswith("\n"):
                            f.write("\n")
            else:
                f.write("gparamlist: null\n")
            if actor.profile:
                f.write(f"profile: {actor.profile}\n")
            else:
                f.write("profile: null\n")
            if actor_name in localization:
                l = localization[actor_name]
                err = u.ensure(l.profile == actor.profile, f"Profile mismatch for {actor_name}")
                if err: return err
                f.write("localization:\n")
                for locale in msyt.locale_map:
                    f.write(f"  {locale}:\n")
                    strings = l.strings[locale]
                    name = json.dumps(strings.name)
                    name_attr = json.dumps(strings.name_attr)
                    f.write(f"    name:\n")
                    f.write(f"      text: {name}\n")
                    f.write(f"      attr: {name_attr}\n")
                    desc = json.dumps(strings.desc)
                    f.write(f"    desc: {desc}\n")
                    album_desc = json.dumps(strings.album_desc)
                    f.write(f"    album_desc: {album_desc}\n")
            else:
                f.write("localization: null\n")

    progress.done()
    return None
