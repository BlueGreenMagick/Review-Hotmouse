def test_sort_hotkey_btn() -> None:
    from addon.config import HotkeyTabManager

    h0 = "q_click_right"
    a0 = h0
    assert HotkeyTabManager.sort_hotkey_btn(h0) == a0
    h1 = "q_press_right_press_left_click_middle"
    a1 = "q_press_left_press_right_click_middle"
    assert HotkeyTabManager.sort_hotkey_btn(h1) == a1
    h2 = "a_press_xbutton1_press_right_press_left_wheel_up"
    a2 = "a_press_left_press_right_press_xbutton1_wheel_up"
    assert HotkeyTabManager.sort_hotkey_btn(h2) == a2
    h3 = "q_press_right_click_left"
    a3 = h3
    assert HotkeyTabManager.sort_hotkey_btn(h3) == a3
