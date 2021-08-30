from typing import Callable, Dict, Any
from pathlib import Path
from unittest.mock import Mock
import pytest
import json
import sys

import aqt
import aqt.utils
from aqt.addons import AddonMeta

project_path = Path(__file__).parent.parent
addon_path = project_path / "addon"
sys.path.append(str(project_path))


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

    def setWebExports(self, module: str, pattern: str) -> None:
        return None


@pytest.fixture(autouse=True)
def mock_addonmanager(monkeypatch: Any) -> None:
    """Mock mw.addonManager"""
    mw = Mock()
    mw.configure_mock(addonManager=MockAddonManager())
    monkeypatch.setattr(aqt, "mw", mw)


@pytest.fixture(autouse=True)
def dont_show_aqt_utils_gui() -> None:
    for fn_name in ("showText", "showInfo"):
        setattr(aqt.utils, fn_name, lambda *_, **__: None)
