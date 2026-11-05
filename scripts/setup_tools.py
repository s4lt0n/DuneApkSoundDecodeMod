"""Download pinned Java tools from upstream release pages and verify SHA-256."""
from urllib.request import urlopen
import os
from project import path, read_json, sha256


def main():
    for name, item in read_json(path("tools.json")).items():
        target = path(item["file"])
        if target.is_file() and sha256(target) == item["sha256"]:
            print(f"{name}: already verified")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".download")
        try:
            with urlopen(item["url"], timeout=60) as response, temporary.open("wb") as output:
                while block := response.read(1024 * 1024):
                    output.write(block)
            if sha256(temporary) != item["sha256"]:
                raise ValueError(f"Upstream checksum mismatch: {name}")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        print(f"{name}: downloaded and verified")


if __name__ == "__main__":
    main()
