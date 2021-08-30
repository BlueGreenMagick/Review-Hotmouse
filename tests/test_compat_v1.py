def test_v1_compat() -> None:
    from aqt import mw
    from addon.compat.v1 import v1_compat

    old_config = {
        "q_press_left_press_right_press_middle": "off",  # press
        "q_wheel_down": "",  # empty
        "q_click_right": "good",  # normal
        "a_click_right": "undo",  # normal
        "a_click_xbutton3": "again",
        "a_click_left": "strange_looking_action",
        "a_strange_looking_hotkey": "good",
        "threshold_wheel_ms": 200,
        "tooltip": False,
        "z_debug": False,
    }
    mw.addonManager.writeConfig(__name__, old_config)
    v1_compat()
    config = mw.addonManager.getConfig(__name__)
    assert config == {
        "shortcuts": {
            "q_press_left_press_right_click_middle": "off",
            "q_wheel_down": "<none>",
            "q_click_right": "good",
            "a_click_right": "undo",
        },
        "threshold_wheel_ms": 200,
        "tooltip": False,
        "z_debug": False,
    }

    # Test that shortcuts don't get deleted
    v1_compat()
    assert config == {
        "shortcuts": {
            "q_press_left_press_right_click_middle": "off",
            "q_wheel_down": "<none>",
            "q_click_right": "good",
            "a_click_right": "undo",
        },
        "threshold_wheel_ms": 200,
        "tooltip": False,
        "z_debug": False,
    }


def test_modify_empty_action_shortcuts() -> None:
    from addon.compat.v1 import modify_empty_action_shortcuts

    shortcuts = {
        "q_wheel_down": "",
        "a_click_left": "<none>",
        "a_click_middle": "easy",
        "a_wheel_up": "",
    }
    modify_empty_action_shortcuts(shortcuts)

    assert shortcuts == {
        "q_wheel_down": "<none>",
        "a_click_left": "<none>",
        "a_click_middle": "easy",
        "a_wheel_up": "<none>",
    }


def test_modify_hotkeys_ending_with_press() -> None:
    from addon.compat.v1 import modify_hotkeys_ending_with_press

    shortcuts = {
        "q_wheel_down_press_left": "easy",
        "a_press_left_press_middle_press_right": "hard",
        "a_press_right_click_right": "<none>",
    }
    modify_hotkeys_ending_with_press(shortcuts)

    assert shortcuts == {
        "q_wheel_down_click_left": "easy",
        "a_press_left_press_middle_click_right": "hard",
        "a_press_right_click_right": "<none>",
    }
