import os
import shutil
import yaml
import zlib
import subprocess
import struct
from typing import Any

def which(name):
    """Find executable in PATH"""
    x = shutil.which(name)
    ensure(x, f"{name} not found in PATH")
    return x

def botw(*args):
    """Get path relative to botw directory"""
    return home("botw", *args)

def output(*args):
    """Get path relative to output directory"""
    return home("output", *args)

def home(*args):
    """Get path relative from script home (repo root)"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), *args)

def relpath(path):
    return os.path.relpath(path, os.getcwd())
            
def ensure(condition, message = "") -> str | None:
    if not condition:
        return f"assertion failed: {message}"
    return None

def fatal(x):
    if x:
        raise Exception(f"fatal: {x}")

def shell(args, cwd = None) -> str | None:
    try:
        subprocess.run(args, cwd=cwd, check=True)
    except Exception as e:
        return str(e)
    return None
        

def abort(message):
    raise Exception(message)

def fopenr(path):
    return open(path, "r", encoding="utf-8")

def fopenw(path):
    return open(path, "w", encoding="utf-8", newline="\n")

def extend_yaml():
    def dict_ctor(loader, node):
        values = loader.construct_mapping(node)
        return dict(values)

    def str_ctor(loader, node):
        values = loader.construct_scalar(node)
        return str(values)

    def int_ctor(loader, node):
        values = loader.construct_scalar(node)
        return int(values, 0)

    def list_ctor(loader, node):
        values = loader.construct_sequence(node)
        return list(values)

    yaml.add_constructor('!list', dict_ctor)
    yaml.add_constructor('!obj', dict_ctor)
    yaml.add_constructor('!io', dict_ctor)
    yaml.add_constructor('!str64', str_ctor)
    yaml.add_constructor('!str32', str_ctor)
    yaml.add_constructor('!str256', str_ctor)
    yaml.add_constructor('!vec3', list_ctor)
    yaml.add_constructor('!u', int_ctor)

extend_yaml()

def fyaml(path) -> tuple[Any, str | None]:
    try:
        with fopenr(path) as f:
            return yaml.load(f, yaml.FullLoader), None
    except Exception as e:
        return None, str(e)

def sfget[T](obj: Any, key: str, typ: type[T]) -> tuple[T, str | None]:
    if not isinstance(obj, dict):
        return None, "not a dictionary" # type: ignore
    if key not in obj:
        return None, f"missing key: {key}" # type: ignore
    x = obj[key]
    if not isinstance(x, typ):
        return None, f"invalid type: {key}" # type: ignore
    return x, None

def sfgetopt[T](obj: Any, key: str, typ: type[T]) -> tuple[T | None, str | None]:
    if key not in obj:
        return None, None
    return sfget(obj, key, typ)

def pool():
    import multiprocessing
    return multiprocessing.Pool()

def check_errors(errors: list[str]) -> str | None:
    if not errors:
        return None
    for err in errors:
        print(f"error: {err}")
    return f"{len(errors)} errors found"

def clean_dir(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def crc32(s: str) -> int:
    return zlib.crc32(bytes(s, "utf-8"))

def hex08(x: int) -> str:
    return f"0x{x:08x}"

def f32_bits(x: int) -> float:
    return struct.unpack('<f', struct.pack('<I', x))[0]
