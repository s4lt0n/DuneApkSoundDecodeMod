"""Print original:mod mappings from the single release catalog."""
from project import catalog


if __name__ == "__main__":
    data, _, _ = catalog()
    print("Original | Mod revision | Android versionCode | APK")
    for mod in data["mods"]:
        current = " *" if mod["id"] == data["current"] else ""
        print(f'{mod["original"]} | {mod["revision"]}{current} | {mod["versionCode"]} | {mod["file"]}')
