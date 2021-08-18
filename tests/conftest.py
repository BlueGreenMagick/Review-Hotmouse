from typing import Callable, Dict, Any, Iterator
from pathlib import Path
from pytest_anki import anki_running, AnkiSession
import pytest
import json
import sys

import aqt
import aqt.utils
from aqt.addons import AddonMeta

project_path = Path(__file__).parent.parent
addon_path = project_path / "addon"
sys.path.append(str(project_path))

# Not sure why, but is needed to remove errors.
@pytest.fixture(scope="session", autouse=True)
def anki_session(request: Any) -> Iterator[AnkiSession]:
    param = getattr(request, "param", None)
    with anki_running() if not param else anki_running(**param) as session:
        yield session


class MockAddonManager:
    def __init__(self) -> None:
        config_path = addon_path / "config.json"
        manifest_path = addon_path / "manifest.json"
        config_json_str = config_path.read_text()
        self.default_config = json.loads(config_json_str)
        self.config = json.loads(config_json_str)  # seperate dict obj
        self.meta = json.loads(manifest_path.read_text())
        self.meta["config"] = self.config

    def getConfig(self, module: str) -> Dict[str, Any]:
        return self.config

    def writeConfig(self, module: str, data: Dict[str, Any]) -> None:
        self.config = data

    def addonFromModule(self, module: str) -> str:
        return module.split(".")[0]

    def addonMeta(self, module: str) -> Dict[str, Any]:
        self.meta["config"] = self.config
        return self.meta

    def addon_meta(self, module: str) -> AddonMeta:
        return AddonMeta.from_json_meta(module, self.addonMeta(module))

    def addonConfigDefaults(self, module: str) -> Dict[str, Any]:
        return self.default_config

    def setConfigAction(self, module: str, func: Callable) -> None:
        return None


@pytest.fixture(autouse=True)
def mock_addonmanager(monkeypatch: Any, anki_session: Any) -> None:
    """Mock mw.addonManager"""
    addon_manager = MockAddonManager()
    monkeypatch.setattr(anki_session.mw, "addonManager", addon_manager)


@pytest.fixture(scope="session", autouse=True)
def dont_show_aqt_utils_gui() -> None:
    for fn_name in ("showText", "showInfo"):
        setattr(aqt.utils, fn_name, lambda *_, **__: None)