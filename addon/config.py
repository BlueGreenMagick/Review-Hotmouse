from typing import Callable, Optional, List

from aqt.qt import *

from .ankiaddonconfig import *
from .event import ACTIONS, Button


def general_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.add_tab("General")
    tab.number_input(
        "threshold_wheel_ms",
        "Mouse scroll threshold (1000 is 1s)",
        tooltip="How long a delay between subsequent scroll actions?",
        maximum=3000,
    )
    tab.checkbox("tooltip", "When triggered, show action name")
    tab.checkbox("z_debug", "Debugging: Show hotkey on mouse action")
    tab.stretch()


def create_dropdown(
    layout: ConfigLayout,
    current: str,
    options: List[str],
    on_change: Optional[Callable[[ConfigLayout, int, int], None]] = None,
) -> QComboBox:
    """
    on_change takes 2 arguments:
        - index of currently selected dropdown option,
        - index of dropdown in layout.dropdowns
    """
    dropdown = QComboBox()
    dropdown.insertItems(0, options)
    dropdown.setCurrentIndex(options.index(current))
    layout.addWidget(dropdown)
    if not hasattr(layout, "dropdowns"):
        setattr(layout, "dropdowns", [])
    layout.dropdowns.append(dropdown)
    if on_change:
        ddidx = len(layout.dropdowns) - 1
        dropdown.currentIndexChanged.connect(
            lambda optidx, l=layout, d=ddidx: on_change(l, optidx, d)
        )
    return dropdown


def hotkey_tabs(conf_window: ConfigWindow) -> None:
    button_opts = [b.name for b in Button]
    action_opts = list(ACTIONS.keys())
    mode_opts = ["press", "click", "wheel"]
    wheel_opts = ["up", "down"]

    def on_mode_change(layout: ConfigLayout, optidx: int, ddidx: int) -> None:
        """Handler for when mode dropdown changes"""
        mode = mode_opts[optidx]
        if mode == "press":
            layout.removeWidget(layout.dropdowns.pop(ddidx + 1))
            create_dropdown(layout, button_opts[0], button_opts)
            create_dropdown(layout, "click", mode_opts, on_mode_change)
            create_dropdown(layout, button_opts[0], button_opts)
        else:
            while len(layout.dropdowns) > ddidx + 1:
                # make this the last dropdown
                layout.removeWidget(layout.dropdowns.pop())
            if mode == "click":
                create_dropdown(layout, button_opts[0], button_opts)
            else:  # mode == "wheel"
                create_dropdown(layout, wheel_opts[0], wheel_opts)

    def hotkey_layout(hotkey: str) -> Optional[ConfigLayout]:
        """ hotkey eg: `press_left_click_right`. Without `q_` or `a_`. """
        layout = ConfigLayout(conf_window, QBoxLayout.LeftToRight)

        hotkeylist = hotkey.split("_")
        while len(hotkeylist):
            if len(hotkeylist) == 1:
                return None
            mode = hotkeylist.pop(0)
            btn = hotkeylist.pop(0)
            if mode not in mode_opts:
                return None
            if mode == "wheel" and btn not in wheel_opts:
                return None
            if mode in ("press", "click") and btn not in button_opts:
                return None

            create_dropdown(layout, mode, mode_opts, on_mode_change)
            if mode == "wheel":
                create_dropdown(layout, btn, wheel_opts)
            else:
                create_dropdown(layout, btn, button_opts)
        return layout

    def action_layout(action: str) -> Optional[ConfigLayout]:
        layout = ConfigLayout(conf_window, QBoxLayout.LeftToRight)
        layout.stretch()
        layout.text("&nbsp;<b>→</b>&nbsp;", html=True)
        create_dropdown(layout, action, action_opts)
        return layout

    def build_row(rows_layout: ConfigLayout, hotkey: str, action: str) -> None:
        hlay = hotkey_layout(hotkey)
        alay = action_layout(action)
        if hlay and alay:
            container = QWidget()
            layout = ConfigLayout(conf_window, QBoxLayout.LeftToRight)
            layout.setContentsMargins(0, 4, 2, 4)  # decrease margin
            container.setLayout(layout)
            rows_layout.addWidget(container)
            layout.addLayout(hlay)
            layout.addLayout(alay)
            label = QLabel("&nbsp;<a href='/' style='text-decoration:none;'>❌</a>")
            label.setTextFormat(Qt.RichText)
            layout.addWidget(label)

            def remove(l: str) -> None:
                rows_layout.removeWidget(container)
                container.deleteLater()

            label.linkActivated.connect(remove)

    def add_tab() -> None:
        if conf_window.main_tab.count() > 1:
            conf_window.main_tab.widget(2).deleteLater()
            conf_window.main_tab.widget(1).deleteLater()
            conf_window.main_tab.removeTab(2)
            conf_window.main_tab.removeTab(1)

        q_tab = conf_window.add_tab("Question Side Hotkeys")
        a_tab = conf_window.add_tab("Answer Side Hotkeys")
        q_rows_layout = q_tab.vlayout()
        a_rows_layout = a_tab.vlayout()
        hotkeys = conf.get("hotkeys")
        for hotkey in hotkeys:
            if hotkey[0] == "q":
                build_row(q_rows_layout, hotkey[2:], hotkeys[hotkey])
            elif hotkey[0] == "a":
                build_row(a_rows_layout, hotkey[2:], hotkeys[hotkey])
            else:
                continue
        for tab in (q_tab, a_tab):
            btn_layout = tab.hlayout()
            add_btn = QPushButton("+  Add New ")
            add_btn.clicked.connect(
                lambda _, rows=tab.itemAt(0): build_row(rows, "click_right", "<none>")
            )
            add_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            add_btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn_layout.addWidget(add_btn)
            btn_layout.stretch()
            btn_layout.setContentsMargins(0, 20, 0, 5)
            tab.setSpacing(0)
            tab.addLayout(btn_layout)
            tab.stretch()

    conf_window.widget_updates.append(add_tab)


conf = ConfigManager()
conf.use_custom_window()
conf.add_config_tab(general_tab)
conf.on_window_open(hotkey_tabs)