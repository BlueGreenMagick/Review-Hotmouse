from aqt import mw
from pathlib import Path

config = mw.addonManager.getConfig(__name__)


class Version:
    def __init__(self) -> None:
        self.load()

    def load(self) -> None:
        self.major = config["version"]["major"]
        self.minor = config["version"]["minor"]

    def __eq__(self, other: str) -> bool:  # type: ignore
        ver = [int(i) for i in other.split(".")]
        return self.major == ver[0] and self.minor == ver[1]

    def __gt__(self, other: str) -> bool:
        ver = [int(i) for i in other.split(".")]
        return self.major > ver[0] or (self.major == ver[0] and self.minor > ver[1])

    def __lt__(self, other: str) -> bool:
        ver = [int(i) for i in other.split(".")]
        return self.major < ver[0] or (self.major == ver[0] and self.minor < ver[1])

    def __ge__(self, other: str) -> bool:
        return self == other or self > other

    def __le__(self, other: str) -> bool:
        return self == other or self < other


# version of the add-on prior to running this script
version = Version()

# Save current version
version_file = Path(__file__).parent / "VERSION"
version_string = version_file.read_text()
config["version"]["major"] = int(version_string.split(".")[0])
config["version"]["minor"] = int(version_string.split(".")[1])

####################################################################
