"""Shared, portable paths and catalog validation for build and verification."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def path(value):
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Expected a repository-relative path: {value}")
    resolved = ROOT / relative
    if not resolved.resolve().is_relative_to(ROOT):
        raise ValueError(f"Path escapes repository: {value}")
    return resolved


def relative(value):
    return Path(value).relative_to(ROOT).as_posix()


def sha256(value):
    digest = hashlib.sha256()
    with Path(value).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(value):
    return json.loads(Path(value).read_text(encoding="utf-8"))


def write_json(value, data):
    Path(value).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def catalog(release=None):
    data = read_json(path("versions.json"))
    if data.get("schemaVersion") != 1:
        raise ValueError("Unsupported versions.json schema")
    originals = {item["version"]: item for item in data["originals"]}
    mods = {item["id"]: item for item in data["mods"]}
    if len(originals) != len(data["originals"]) or len(mods) != len(data["mods"]):
        raise ValueError("Duplicate original version or mod ID")
    if len({item["file"] for item in data["mods"]}) != len(mods):
        raise ValueError("Each mod must have a separate artifact path")
    codes = set()
    previous_code = 0
    for item in data["originals"]:
        path(item["file"])
    for item in data["mods"]:
        if item["original"] not in originals or item["revision"] < 1:
            raise ValueError("Unknown original or invalid revision")
        if item["id"] != f'{item["original"]}:{item["revision"]}':
            raise ValueError("Mod ID must be original:revision")
        if item["versionCode"] in codes:
            raise ValueError("Android versionCode must be unique across mod releases")
        if item["versionCode"] <= previous_code:
            raise ValueError("List mod releases in increasing Android versionCode order")
        codes.add(item["versionCode"])
        previous_code = item["versionCode"]
        path(item["file"])
        path(item["recipe"])
    key = release or data["current"]
    if key not in mods:
        raise ValueError(f"Unknown release: {key}")
    return data, mods[key], originals[mods[key]["original"]]


def run(args, cwd=None):
    completed = subprocess.run(
        [str(arg) for arg in args], cwd=cwd or ROOT, check=False,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    output = completed.stdout.replace(str(ROOT), ".")
    if output:
        print(output, end="" if output.endswith("\n") else "\n", flush=True)
    if completed.returncode:
        raise RuntimeError(f"{args[0]} failed with exit code {completed.returncode}")
    return output


def tools():
    configured = read_json(path("tools.json"))
    for item in configured.values():
        local = path(item["file"])
        if not local.is_file():
            raise FileNotFoundError("Run python3 scripts/setup_tools.py first")
        if sha256(local) != item["sha256"]:
            raise ValueError(f"Tool checksum mismatch: {item['file']}")
    return {name: item["file"] for name, item in configured.items()}
