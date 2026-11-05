"""Reassemble the ARM shim and check it against the versioned reference blob."""
import argparse
import struct
from project import catalog, path, read_json, relative, run, sha256


def main(release=None):
    from elftools.elf.elffile import ELFFile
    _, mod, _ = catalog(release)
    recipe_dir = path(mod["recipe"])
    native = read_json(recipe_dir / "recipe.json")["native"]
    obj = path(".build/checks/menu-shim.o")
    obj.parent.mkdir(parents=True, exist_ok=True)
    run(["clang", "-target", "armv7-none-linux-gnueabihf", "-c",
         relative(recipe_dir / "native/menu-shim.s"), "-o", relative(obj)])
    with obj.open("rb") as stream:
        code = bytearray(ELFFile(stream).get_section_by_name(".text").data())
    targets = [native["originalCallTarget"], native["originalCallTarget"], native["javaBridgeAddress"]]
    calls = 0
    for offset in range(0, 128, 4):
        instruction = struct.unpack_from("<I", code, offset)[0]
        if instruction & 0xFF000000 == 0xEB000000:
            address = native["shimAddress"] + offset
            delta = targets[calls] - address - 8
            assert delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25)
            struct.pack_into("<I", code, offset, 0xEB000000 | ((delta >> 2) & 0xFFFFFF))
            calls += 1
    assert calls == len(targets)
    blob = recipe_dir / native["shim"]
    assert sha256(blob) == native["shimSha256"]
    assert code == blob.read_bytes(), "Assembly and committed native blob differ"
    print(f"PASS: native assembly matches {len(code)}-byte reference blob")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release")
    main(parser.parse_args().release)
