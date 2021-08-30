from typing import Dict, Tuple

from aqt import mw
from aqt.utils import showText

from ..event import Button, ACTION_OPTS


def v1_compat() -> None:
    """Compat code from v1.

    Change hotkeys ending in 'press' to 'click'
    Change action "" to <none>
    Remove shortcuts using xbutton 2-9
    Remove shortcuts with invalid hotkey or action strings
    Inform user if their hotkeys are modified.
    """
    shortcuts = get_and_remove_v1_shortcuts_from_config()
    modify_empty_action_shortcuts(shortcuts)
    (modified, removed) = modify_hotkeys_ending_with_press(shortcuts)
    removed2 = remove_invalid_shortcuts(shortcuts)
    removed.update(removed2)
    config = mw.addonManager.getConfig(__name__)
    config["shortcuts"] = shortcuts
    mw.addonManager.writeConfig(__name__, config)
    if modified or removed:
        inform_v1_shortcuts_modified(modified, removed)


def get_and_remove_v1_shortcuts_from_config() -> Dict[str, str]:
    """Remove and returns shortcut config entries. Including config["shortcuts"]"""
    config = mw.addonManager.getConfig(__name__)
    shortcuts = {}
    config_keys = [
        "threshold_wheel_ms",
        "threshold_angle",
        "tooltip",
        "z_debug",
        "version",
        "shortcuts",
    ]

    for key in config:
        if key in config_keys:
            continue
        shortcuts[key] = config[key]
    for key in shortcuts:
        config.pop(key)
    if "shortcuts" in config:
        existing_shortcuts = config["shortcuts"]
        for hotkey in existing_shortcuts:
            shortcuts[hotkey] = existing_shortcuts[hotkey]
    mw.addonManager.writeConfig(__name__, config)
    return shortcuts


def modify_empty_action_shortcuts(shortcuts: Dict[str, str]) -> None:
    """Changes "" action to "<none>"."""
    for hotkey in shortcuts:
        if shortcuts[hotkey] == "":
            shortcuts[hotkey] = "<none>"


def modify_hotkeys_ending_with_press(
    shortcuts: Dict[str, str]
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Modifies hotkeys ending with "press" to "click". Returns modified.

    If another shortcut ending with "click" exists, it is skipped.
    """
    modified = {}
    removed = {}

    to_modify = {}
    for hotkey in shortcuts:
        hotkeylist = hotkey.split("_")
        if len(hotkeylist) < 2:
            continue
        new_hotkey = hotkey
        if hotkeylist[-2] == "press":
            hotkeylist[-2] = "click"
            new_hotkey = "_".join(hotkeylist)
            to_modify[hotkey] = new_hotkey

    for hotkey in to_modify:
        new_hotkey = to_modify[hotkey]
        if new_hotkey in shortcuts:
            removed[hotkey] = shortcuts.pop(hotkey)
        else:
            shortcuts[new_hotkey] = shortcuts.pop(hotkey)
            modified[hotkey] = new_hotkey

    return (modified, removed)


def is_valid_hotkey(hotkey: str) -> bool:
    """Returns True if hotkey string is valid."""
    mode_opts = ["press", "click", "wheel"]
    btn_opts = [b.name for b in Button]
    wheel_opts = ["up", "down"]

    hotkeylist = hotkey[2:].split("_")
    if len(hotkeylist) == 0 or len(hotkeylist) % 2 != 0:
        return False
    for i in range(0, len(hotkeylist), 2):
        mode = hotkeylist[i]
        btn = hotkeylist[i + 1]
        if mode not in mode_opts:
            return False
        if mode == "wheel" and btn not in wheel_opts:
            return False
        elif mode in ("press", "click") and btn not in btn_opts:
            return False
    if hotkey[-2] == "press":
        return False
    return True


def is_valid_action(action: str) -> bool:
    """Returns True if action string is valid."""
    if action not in ACTION_OPTS:
        return False
    return True


def remove_invalid_shortcuts(shortcuts: Dict[str, str]) -> Dict[str, str]:
    """Removes shortcuts that has invalid hotkey or action strings. Returns removed."""
    remove = {}
    for hotkey in shortcuts:
        action = shortcuts[hotkey]
        if is_valid_hotkey(hotkey) and is_valid_action(action):
            continue
        remove[hotkey] = ""
    for hotkey in remove:
        remove[hotkey] = shortcuts.pop(hotkey)
    return remove


def inform_v1_shortcuts_modified(mod: Dict[str, str], rem: Dict[str, str]) -> None:
    """Notifies user about how shortcuts were changed.

    - mod: {original_hotkey: new_hotkey}
    - rem: {hotkey: action}
    """
    base = (
        "<h3>Review Hotmouse Update Notes</h3>"
        "Some shortcuts were invalid, and were modified or removed for compatibility. "
        "This may be because the shortcut wasn't valid in the first case, "
        "or it is no longer valid after updating."
        "<br><br>"
        "For example, 'press' only hotkeys are no longer valid "
        "and hotkeys must now contain either 'click' or 'wheel'."
        "<br><br>"
        "If you are not sure why a shortcut was modified or deleted, please create an issue at the "
        '<a href="https://github.com/BlueGreenMagick/Review-Hotmouse/issues">Github repo</a>.'
        "<br>"
        "{mod}"
        "<br>"
        "{rem}"
    )
    mod_msg = ""
    rem_msg = ""
    if mod:
        mod_msg = "<br><b>List of modified hotkeys:</b>"
        for hotkey in mod:
            mod_msg += "<br>"
            mod_msg += f"{hotkey} → {mod[hotkey]}"
    if rem:
        rem_msg = "<br><b>List of deleted hotkeys:</b>"
        for hotkey in rem:
            rem_msg += "<br>"
            rem_msg += f"{hotkey}: {rem[hotkey]}"
    msg = base.format(mod=mod_msg, rem=rem_msg)
    showText(msg, mw, type="html", title="Review Hotmouse", copyBtn=True)
