"""Check APK identity, signature, source mapping, resources and permitted native edits."""
import argparse
import hashlib
import io
import struct
import xml.etree.ElementTree as ET
import zipfile
from project import catalog, path, read_json, relative, run, sha256, tools


def verify(apk_path=None, release=None, check_catalog_hash=True):
    if not __debug__:
        raise RuntimeError("Run verification without Python -O; assertion checks are required")
    from loguru import logger
    logger.remove()
    from androguard.core.apk import APK
    from androguard.core.dex import DEX

    data, mod, original = catalog(release)
    apk_path = apk_path or path(mod["file"])
    if check_catalog_hash and (not mod["sha256"] or sha256(apk_path) != mod["sha256"]):
        raise ValueError("Mod APK does not match the catalog checksum")
    if sha256(path(original["file"])) != original["sha256"]:
        raise ValueError("Original APK does not match the catalog checksum")
    recipe_dir = path(mod["recipe"])
    recipe = read_json(recipe_dir / "recipe.json")
    configured = tools()
    run(["java", "-jar", configured["signer"], "--apks", relative(apk_path),
         "--onlyVerify", "--verifySha256", data["signing"]["certificateSha256"]])
    apk = APK(str(apk_path))
    original_apk = APK(str(path(original["file"])))
    assert original_apk.get_package() == original["package"]
    assert original_apk.get_androidversion_name() == original["version"]
    assert int(original_apk.get_androidversion_code()) == original["versionCode"]
    assert apk.get_package() == mod["package"]
    assert apk.get_androidversion_name() == mod["versionName"]
    assert int(apk.get_androidversion_code()) == mod["versionCode"]
    assert apk.get_app_name() == recipe["label"]
    assert apk.get_android_resources().get_packages_names() == [mod["package"]]
    assert apk.get_target_sdk_version() == original_apk.get_target_sdk_version()
    assert apk.get_min_sdk_version() == original_apk.get_min_sdk_version()
    certificate = hashlib.sha256(apk.get_certificates()[0].dump()).hexdigest()
    assert certificate == data["signing"]["certificateSha256"]
    ns = "{http://schemas.android.com/apk/res/android}"
    assert [n.get(ns + "authorities") for n in apk.get_android_manifest_xml().iter("provider")] == [mod["package"] + ".fileprovider"]
    with zipfile.ZipFile(apk_path) as current, zipfile.ZipFile(path(original["file"])) as stock:
        assert current.testzip() is None
        dex = DEX(current.read("classes.dex"))
        clazz = dex.get_class("Lcom/dunehd/shell/internalplayer/VLCPlayerImpl;")
        method = next(m for m in clazz.get_methods() if m.get_name() == "getPassthroughAudioFormatMask")
        instructions = list(method.get_instructions())
        assert sum("DtsPcmSettings;->filterMask" in i.get_output() for i in instructions) == 2
        assert not any(i.get_name() == "and-int/lit16" and "-385" in i.get_output() for i in instructions)
        for name in ["DtsPcmSettings", "DtsPcmSettings$Choice", "DtsPcmSettings$ShowDialog"]:
            assert dex.get_class("Lcom/dunehd/shell/settings/" + name + ";")
        assert not any(recipe["sourcePackage"] in s for s in dex.get_strings())
        helper = dex.get_class("Lcom/dunehd/shell/settings/DtsPcmSettings;")
        filter_method = next(m for m in helper.get_methods() if m.get_name() == "filterMask")
        assert any("isEnabled" in i.get_output() for i in filter_method.get_instructions())
        assert any(i.get_name() == "if-eqz" for i in filter_method.get_instructions())
        audio_config = next(m for m in clazz.get_methods() if m.get_name() == "applyVlcMediaPlayerAudioConfiguration")
        assert any("DtsPcmSettings;->isEnabled" in i.get_output() for i in audio_config.get_instructions())

        libraries = [n for n in stock.namelist() if n.startswith("lib/") and n.endswith(".so")]
        native = recipe["native"]
        for name in libraries:
            if name != native["path"]:
                assert current.read(name) == stock.read(name), name
        before = stock.read(native["path"])
        after = current.read(native["path"])
        assert hashlib.sha256(before).hexdigest() == native["originalSha256"]
        assert len(before) == len(after)
        normalized = bytearray(after)
        source_id = (recipe["sourcePackage"] + "\0").encode()
        target_id = (recipe["targetPackage"] + "\0").encode()
        identity = before.index(source_id)
        assert after[identity:identity + len(source_id)] == target_id
        normalized[identity:identity + len(source_id)] = source_id
        hook, base = native["hookAddress"], native["shimAddress"]
        expected_call = 0xEB000000 | (((base - hook - 8) >> 2) & 0xFFFFFF)
        assert struct.unpack_from("<I", after, hook)[0] == expected_call
        normalized[hook:hook + 4] = before[hook:hook + 4]
        shim = (recipe_dir / native["shim"]).read_bytes()
        assert after[base:base + len(shim)] == shim
        assert not any(before[base:native["paddingEnd"]])
        normalized[base:base + len(shim)] = before[base:base + len(shim)]
        phoff = struct.unpack_from("<I", before, 28)[0]
        entry_size, entries = struct.unpack_from("<HH", before, 42)
        segments = 0
        for index in range(entries):
            offset = phoff + index * entry_size
            kind, file_offset, _, _, _, _, flags, _ = struct.unpack_from("<8I", before, offset)
            if kind == 1 and file_offset == 0 and flags == 5:
                assert struct.unpack_from("<II", after, offset + 16) == (base + len(shim),) * 2
                normalized[offset + 16:offset + 24] = before[offset + 16:offset + 24]
                segments += 1
        assert segments == 1 and normalized == before, "Unexpected native edit outside allowed ranges"

        original_data = zipfile.ZipFile(io.BytesIO(stock.read("assets/data.zip")))
        updated_data = zipfile.ZipFile(io.BytesIO(current.read("assets/data.zip")))
        assert set(updated_data.namelist()) == set(original_data.namelist())
        changes = []
        for name in original_data.namelist():
            old, new = original_data.read(name), updated_data.read(name)
            if name == "firmware/config/apk_app_id.txt":
                assert new == old.replace(recipe["sourcePackage"].encode(), recipe["targetPackage"].encode())
            elif name == "firmware/config/menu_config.xml":
                marker = b'<setting id="hd_audio_bitstream"/>'
                assert new == old.replace(marker, marker + b'\n          <setting id="button_dts_pcm_settings"/>')
            elif name.startswith("firmware/translations/dune_language_") and name.endswith(".txt"):
                assert new.startswith(old) and new.count(b"dts_pcm_setting_label = ") == 1
            else:
                assert new == old, name
            if new != old:
                changes.append(name)
        menu = ET.fromstring(updated_data.read("firmware/config/menu_config.xml"))
        audio = next(n for n in menu.iter("screen") if n.get("id") == "audio" and n.get("type") == "generic")
        settings = [n.get("id") for n in audio.find("settings")]
        assert settings.index("button_dts_pcm_settings") == settings.index("hd_audio_bitstream") + 1
        assert not any(n.endswith("/decode_dts_pcm") for n in updated_data.namelist())
        metadata = current.read("assets/data.inf").decode()
        assert f"variant = {mod['id']}\n" in metadata
        archive_hash = hashlib.sha256(current.read("assets/data.zip")).hexdigest()
        assert f"data_archive_sha256 = {archive_hash}\n" in metadata
        icons = list(path("assets/android").rglob("*.png"))
        assert len(icons) == 16
        for icon in icons:
            name = "res/" + icon.relative_to(path("assets/android")).as_posix()
            assert current.read(name) == icon.read_bytes()
            # Apktool removes the redundant -v4 density qualifier while decoding.
            parent, filename = name.rsplit("/", 1)
            stock_name = name if name in stock.namelist() else parent + "-v4/" + filename
            assert struct.unpack(">II", current.read(name)[16:24]) == struct.unpack(">II", stock.read(stock_name)[16:24])
    return {
        "release": mod["id"], "original": original["version"], "revision": mod["revision"],
        "apk": relative(apk_path), "sha256": sha256(apk_path), "package": mod["package"],
        "versionName": mod["versionName"], "versionCode": mod["versionCode"],
        "certificateSha256": certificate, "publicDevelopmentKey": True,
        "signatureAndAlignmentVerified": True, "nativeShimBytes": len(shim),
        "unchangedNativeLibraries": len(libraries) - 1, "updatedIconsAndBanner": len(icons),
        "audioMenuSettings": settings, "changedEmbeddedDataFiles": len(changes),
        "androidUiTested": False, "devicePlaybackTested": False, "staticChecks": "PASS",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release")
    args = parser.parse_args()
    result = verify(release=args.release)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
