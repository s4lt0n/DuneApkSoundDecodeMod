"""Build a cataloged mod directly from its original APK, without previous releases."""
import argparse
import io
import os
import re
import shutil
import struct
import zipfile
from project import ROOT, catalog, path, read_json, relative, run, sha256, tools, write_json


def branch(address, target):
    delta = target - address - 8
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError("ARM BL target outside encodable range")
    return struct.pack("<I", 0xEB000000 | ((delta >> 2) & 0xFFFFFF))


def patch_native(decoded, recipe_dir, recipe):
    native = recipe["native"]
    library = decoded / native["path"]
    if sha256(library) != native["originalSha256"]:
        raise ValueError("Unsupported native library; port the recipe instead of applying old offsets")
    blob_path = recipe_dir / native["shim"]
    if sha256(blob_path) != native["shimSha256"]:
        raise ValueError("Native shim checksum mismatch")
    data = bytearray(library.read_bytes())
    old = (recipe["sourcePackage"] + "\0").encode()
    new = (recipe["targetPackage"] + "\0").encode()
    if len(old) != len(new) or data.count(old) != 1:
        raise ValueError("Native identity must have one same-length replacement")
    data = data.replace(old, new)
    hook, base, limit = (native[key] for key in ["hookAddress", "shimAddress", "paddingEnd"])
    if data[hook:hook + 4] != branch(hook, native["originalCallTarget"]):
        raise ValueError("Original native call differs from recipe")
    blob = blob_path.read_bytes()
    if len(blob) > limit - base or any(data[base:limit]):
        raise ValueError("Native padding is unavailable")
    data[base:base + len(blob)] = blob
    data[hook:hook + 4] = branch(hook, base)
    phoff = struct.unpack_from("<I", data, 28)[0]
    entry_size, entries = struct.unpack_from("<HH", data, 42)
    extended = 0
    for index in range(entries):
        offset = phoff + index * entry_size
        kind, file_offset, _, _, size, memory_size, flags, _ = struct.unpack_from("<8I", data, offset)
        if kind == 1 and file_offset == 0 and flags == 5:
            if size != base or memory_size != base:
                raise ValueError("Executable segment does not match recipe")
            struct.pack_into("<II", data, offset + 16, base + len(blob), base + len(blob))
            extended += 1
    if extended != 1:
        raise ValueError("Expected exactly one executable load segment")
    library.write_bytes(data)


def patch_data(decoded, mod, recipe):
    archive = decoded / "assets/data.zip"
    output = io.BytesIO()
    delta = 0
    with zipfile.ZipFile(archive) as original, zipfile.ZipFile(output, "w") as updated:
        for info in original.infolist():
            content = original.read(info.filename)
            before = content
            if info.filename == "firmware/config/apk_app_id.txt":
                if content.strip() != recipe["sourcePackage"].encode():
                    raise ValueError("Unexpected embedded package identity")
                content = content.replace(recipe["sourcePackage"].encode(), recipe["targetPackage"].encode())
            elif info.filename == "firmware/config/menu_config.xml":
                marker = b'<setting id="hd_audio_bitstream"/>'
                if content.count(marker) != 1:
                    raise ValueError("Expected one HD audio setting")
                content = content.replace(marker, marker + b'\n          <setting id="button_dts_pcm_settings"/>')
            elif info.filename.startswith("firmware/translations/dune_language_") and info.filename.endswith(".txt"):
                russian = info.filename.endswith("_russian.txt")
                label = "Декодирование DTS:" if russian else "DTS decoding:"
                button = "Настроить" if russian else "Configure"
                content += f"\ndts_pcm_setting_label = {label}\ndts_pcm_setting_button = {button}\n".encode()
            delta += len(content) - len(before)
            updated.writestr(info, content)
    archive.write_bytes(output.getvalue())
    info_file = decoded / "assets/data.inf"
    metadata = info_file.read_text(encoding="utf-8")
    metadata, count = re.subn(
        r"(?m)^bytesCount = (\d+)$", lambda match: f"bytesCount = {int(match[1]) + delta}", metadata,
    )
    if count != 1:
        raise ValueError("Unexpected embedded data metadata")
    # Original cksum is a legacy producer token; the new archive has an explicit SHA-256.
    metadata += f"variant = {mod['id']}\ndata_archive_sha256 = {sha256(archive)}\n"
    info_file.write_text(metadata, encoding="utf-8")


def build(release=None, record=False):
    data, mod, original = catalog(release)
    configured = tools()
    original_apk = path(original["file"])
    if sha256(original_apk) != original["sha256"]:
        raise ValueError("Original APK checksum mismatch")
    recipe_dir = path(mod["recipe"])
    recipe = read_json(recipe_dir / "recipe.json")
    if recipe["originalSha256"] != original["sha256"] or recipe["targetPackage"] != mod["package"]:
        raise ValueError("Recipe does not match selected original/mod")
    work = path(f".build/{mod['original']}/mod-{mod['revision']}")
    work.mkdir(parents=True, exist_ok=True)
    decoded = work / "decoded"
    run(["java", "-jar", configured["apktool"], "d", "-f", "-p", ".build/framework",
         "-o", relative(decoded), original["file"]])
    patch_file = os.path.relpath(recipe_dir / "app.patch", decoded)
    run(["patch", "-p1", "-t", "-i", patch_file], cwd=decoded)
    shutil.copytree(recipe_dir / "overlay", decoded, dirs_exist_ok=True)
    shutil.copytree(path("assets/android"), decoded / "res", dirs_exist_ok=True)
    yaml = decoded / "apktool.yml"
    text = yaml.read_text(encoding="utf-8")
    text, codes = re.subn(r"(?m)^  versionCode:.*$", f"  versionCode: {mod['versionCode']}", text)
    text, names = re.subn(r"(?m)^  versionName:.*$", f"  versionName: {mod['versionName']}", text)
    if codes != 1 or names != 1:
        raise ValueError("Unexpected Apktool version metadata")
    yaml.write_text(text, encoding="utf-8")
    patch_native(decoded, recipe_dir, recipe)
    patch_data(decoded, mod, recipe)
    unsigned = work / "unsigned.apk"
    run(["java", "-jar", configured["apktool"], "b", "--no-crunch", "-p", ".build/framework",
         relative(decoded), "-o", relative(unsigned)])
    signed_dir = work / "signed"
    if signed_dir.exists():
        shutil.rmtree(signed_dir)
    key = data["signing"]
    password = path(key["passwordFile"]).read_text(encoding="utf-8").strip()
    run(["java", "-jar", configured["signer"], "--apks", relative(unsigned),
         "--out", relative(signed_dir), "--ks", key["keystore"], "--ksAlias", key["alias"],
         "--ksPass", password, "--ksKeyPass", password])
    candidates = list(signed_dir.glob("*.apk"))
    if len(candidates) != 1:
        raise ValueError("Expected exactly one signed APK")
    from verify import verify
    report = verify(candidates[0], mod["id"], check_catalog_hash=False)
    write_json(work / "verification.json", report)
    if record:
        destination = path(mod["file"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidates[0], destination)
        mod["sha256"] = sha256(destination)
        write_json(path("versions.json"), data)
        report["apk"] = mod["file"]
        write_json(work / "verification.json", report)
        if mod["id"] == data["current"]:
            write_json(path("docs/verification.json"), report)
        print(f"Recorded {mod['id']}: {mod['file']}")
    else:
        print(f"Built {relative(candidates[0])}; versions.json unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", help="Catalog original:revision; default is current")
    parser.add_argument("--record", action="store_true", help="Copy APK to catalog path and record SHA-256")
    options = parser.parse_args()
    build(options.release, options.record)
