from typing import NamedTuple, Optional, List, Tuple, Union, Literal

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


class Options(NamedTuple):
    mode: List[str]
    button: List[str]
    wheel: List[str]
    action: List[str]


OPTS = Options(
    ["press", "click", "wheel"],
    [b.name for b in Button],
    ["up", "down"],
    list(ACTIONS.keys()),
)


class DDConfigLayout(ConfigLayout):
    def __init__(self, conf_window: ConfigWindow):
        super().__init__(conf_window, QBoxLayout.LeftToRight)
        self.dropdowns: List[QComboBox] = []

    def create_dropdown(
        self, current: str, options: List[str], is_mode: bool = False
    ) -> QComboBox:
        """
        on_change takes 2 arguments:
            - index of currently selected dropdown option,
            - index of dropdown in layout.dropdowns
        """
        dropdown = QComboBox()
        dropdown.insertItems(0, options)
        dropdown.setCurrentIndex(options.index(current))
        self.addWidget(dropdown)
        self.dropdowns.append(dropdown)
        if is_mode:
            ddidx = len(self.dropdowns) - 1
            dropdown.currentIndexChanged.connect(
                lambda optidx, d=ddidx: self.on_mode_change(optidx, d)
            )
        return dropdown

    def on_mode_change(self, optidx: int, ddidx: int) -> None:
        """Handler for when mode dropdown changes"""
        mode = OPTS.mode[optidx]
        dropdowns = self.dropdowns
        if mode == "press":
            self.removeWidget(dropdowns.pop(ddidx + 1))
            self.create_dropdown(OPTS.button[0], OPTS.button)
            self.create_dropdown("click", OPTS.mode, is_mode=True)
            self.create_dropdown(OPTS.button[0], OPTS.button)
        else:
            while len(dropdowns) > ddidx + 1:
                # make this the last dropdown
                self.removeWidget(dropdowns.pop())
            if mode == "click":
                self.create_dropdown(OPTS.button[0], OPTS.button)
            else:  # mode == "wheel"
                self.create_dropdown(OPTS.wheel[0], OPTS.wheel)


class HotkeyTabManager:
    def __init__(
        self, tab: ConfigLayout, side: Union[Literal["q"], Literal["a"]]
    ) -> None:
        self.tab = tab
        self.config_window = tab.config_window
        self.side = side
        # [ ( [mode, button, ...], [action]), ... ]
        self.layouts: List[Tuple[DDConfigLayout, DDConfigLayout]] = []
        self.setup_tab()

    def setup_tab(self) -> None:
        tab = self.tab
        self.rows_layout = self.tab.vlayout()
        btn_layout = tab.hlayout()
        add_btn = QPushButton("+  Add New ")
        add_btn.clicked.connect(
            lambda _: self.add_row(f"{self.side}_click_right", "<none>")
        )
        add_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn_layout.addWidget(add_btn)
        btn_layout.stretch()
        btn_layout.setContentsMargins(0, 20, 0, 5)
        tab.setSpacing(0)
        tab.addLayout(btn_layout)
        tab.stretch()

    def create_layout(self) -> DDConfigLayout:
        return DDConfigLayout(self.config_window)

    def clear_rows(self) -> None:
        """Clear all rows in tab. Run before setup_rows."""
        for i in range(self.rows_layout.count()):
            widget = self.rows_layout.itemAt(0).widget()
            self.rows_layout.removeWidget(widget)
            widget.deleteLater()

    def setup_rows(self) -> None:
        hotkeys = conf.get("hotkeys")
        for hotkey in hotkeys:
            if hotkey[0] == self.side:
                self.add_row(hotkey, hotkeys[hotkey])

    def hotkey_layout(self, hotkey: str) -> Optional[DDConfigLayout]:
        """ hotkey eg: `q_press_left_click_right`. Returns None if hotkey is invalid. """

        layout = self.create_layout()
        hotkeylist = hotkey[2:].split("_")
        if len(hotkeylist) % 2 != 0:
            return None
        for i in range(0, len(hotkeylist), 2):
            mode = hotkeylist[i]
            btn = hotkeylist[i + 1]
            if mode not in OPTS.mode:
                return None
            if mode == "wheel" and btn not in OPTS.wheel:
                return None
            if mode in ("press", "click") and btn not in OPTS.button:
                return None

            layout.create_dropdown(mode, OPTS.mode, is_mode=True)
            if mode == "wheel":
                layout.create_dropdown(btn, OPTS.wheel)
            else:
                layout.create_dropdown(btn, OPTS.button)
        return layout

    def action_layout(self, action: str) -> Optional[DDConfigLayout]:
        """Returns None if action string is invalid."""
        if action not in OPTS.action:
            return None
        layout = self.create_layout()
        layout.stretch()
        layout.text("&nbsp;<b>→</b>&nbsp;", html=True)
        layout.create_dropdown(action, OPTS.action)
        return layout

    def add_row(self, hotkey: str, action: str) -> None:
        hlay = self.hotkey_layout(hotkey)
        alay = self.action_layout(action)
        if hlay and alay:
            container = QWidget()
            layout = self.create_layout()
            layout.setContentsMargins(0, 4, 2, 4)  # decrease margin
            container.setLayout(layout)
            self.rows_layout.addWidget(container)
            layout.addLayout(hlay)
            layout.addLayout(alay)
            label = QLabel("&nbsp;<a href='/' style='text-decoration:none;'>❌</a>")
            label.setTextFormat(Qt.RichText)
            layout.addWidget(label)

            def remove(l: str) -> None:
                self.rows_layout.removeWidget(container)
                container.deleteLater()

            label.linkActivated.connect(remove)

    def on_update(self) -> None:
        self.clear_rows()
        self.setup_rows()

    def on_save(self) -> None:
        pass


def hotkey_tabs(conf_window: ConfigWindow) -> None:
    q_tab = conf_window.add_tab("Question Hotkeys")
    q_manager = HotkeyTabManager(q_tab, "q")
    a_tab = conf_window.add_tab("AnswerHotkeys")
    a_manager = HotkeyTabManager(a_tab, "a")
    conf_window.widget_updates.append(q_manager.on_update)
    conf_window.widget_updates.append(a_manager.on_update)


conf = ConfigManager()
conf.use_custom_window()
conf.add_config_tab(general_tab)
conf.add_config_tab(hotkey_tabs)