import re
import sys
import simplejson
from pathlib import Path

version_string = sys.argv[1]
assert re.match(r"^(\d+).(\d+)$", version_string)
addon_root = Path(sys.argv[2])
assert addon_root.is_dir()


manifest_path = addon_root / "manifest.json"
# Write version in manifest.json
with manifest_path.open("r") as f:
    manifest = simplejson.load(f)

with manifest_path.open("w") as f:
    manifest["human_version"] = version_string
    simplejson.dump(manifest, f, indent=2)

# human_version is only updated on install.
# For developing purposes, use VERSION file to check current version
version_path = addon_root / "VERSION"
version_path.write_text(version_string)
