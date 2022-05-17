from typing import NamedTuple, Optional, List, Dict, Tuple, Union, Literal

from aqt.qt import *

from .ankiaddonconfig import *
from .event import ACTION_OPTS, Button, refresh_config


def general_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.add_tab("General")
    tab.number_input(
        "threshold_wheel_ms",
        "Mouse scroll threshold (1000 is 1s)",
        tooltip="How long a delay between subsequent scroll actions?",
        maximum=3000,
    )
    tab.checkbox(
        "default_enabled",
        "add-on is enabled at start",
        "If you uncheck this box, the add-on will start as turned off when Anki is launched",
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
    mode=["press", "click", "wheel"],
    button=[b.name for b in Button],
    wheel=["up", "down"],
    action=ACTION_OPTS,
)


class DDConfigLayout(ConfigLayout):
    def __init__(self, conf_window: ConfigWindow):
        super().__init__(conf_window, QBoxLayout.Direction.LeftToRight)
        self.dropdowns: List[QComboBox] = []

    def create_dropdown(
        self, current: str, options: List[str], is_mode: bool = False
    ) -> QComboBox:
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
            dd = dropdowns.pop(ddidx + 1)
            self.removeWidget(dd)
            dd.deleteLater()
            self.create_dropdown(OPTS.button[0], OPTS.button)
            self.create_dropdown("click", OPTS.mode, is_mode=True)
            self.create_dropdown(OPTS.button[0], OPTS.button)
        else:
            while len(dropdowns) > ddidx + 1:
                # make this the last dropdown
                dd = dropdowns.pop()
                self.removeWidget(dd)
                dd.deleteLater()
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
        # For each row, (hotkey_layout, action_layout)
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
        add_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_layout.addWidget(add_btn)
        btn_layout.stretch()
        btn_layout.setContentsMargins(0, 20, 0, 5)
        tab.setSpacing(0)
        tab.addLayout(btn_layout)
        tab.stretch()
        tab.space(10)
        tab.text("If you set duplicate hotkeys, only the last one will be saved.")

    def create_layout(self) -> DDConfigLayout:
        return DDConfigLayout(self.config_window)

    def clear_rows(self) -> None:
        """Clear all rows in tab. Run before setup_rows."""
        for i in range(self.rows_layout.count()):
            widget = self.rows_layout.itemAt(0).widget()
            self.rows_layout.removeWidget(widget)
            widget.deleteLater()
            self.layouts = []

    def setup_rows(self) -> None:
        hotkeys = conf.get("shortcuts")
        for hotkey in hotkeys:
            if hotkey[0] == self.side:
                self.add_row(hotkey, hotkeys[hotkey])

    def hotkey_layout(self, hotkey: str) -> Optional[DDConfigLayout]:
        """hotkey eg: `q_press_left_click_right`. Returns None if hotkey is invalid."""
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
        act_opts = OPTS.action
        layout.create_dropdown(action, act_opts)
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
            layout_tuple = (hlay, alay)
            self.layouts.append(layout_tuple)
            label = QLabel(
                "&nbsp;<a href='/' style='text-decoration:none; color: red;'>⌫</a>"
            )
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setToolTip("Delete this shortcut.")
            layout.addWidget(label)

            def remove(l: str, layouts: Tuple[DDConfigLayout, DDConfigLayout]) -> None:
                self.rows_layout.removeWidget(container)
                container.deleteLater()
                self.layouts.remove(layouts)

            label.linkActivated.connect(lambda l, t=layout_tuple: remove(l, t))

    def on_update(self) -> None:
        self.clear_rows()
        self.setup_rows()

    def get_data(self, hotkeys_data: Dict[str, str]) -> None:
        """Adds hotkey entries to hotkeys_data dictionary."""
        for row in self.layouts:
            hotkey_layout = row[0]
            action_layout = row[1]
            hotkey_str = self.side  # type: str
            for dd in hotkey_layout.dropdowns:
                hotkey_str += "_" + dd.currentText()
            hotkey_str = self.sort_hotkey_btn(hotkey_str)
            action_str = action_layout.dropdowns[0].currentText()
            hotkeys_data[hotkey_str] = action_str

    @staticmethod
    def sort_hotkey_btn(hotkey_str: str) -> str:
        """Sort button order for 'press' in hotkey_str."""
        hotkeylist = hotkey_str.split("_")
        if len(hotkeylist) - 1 <= 4:
            # Doesn't have multiple 'press'
            return hotkey_str
        btns = []
        btn_names = [b.name for b in Button]
        for i in range(1, len(hotkeylist) - 2, 2):
            btn = hotkeylist[i + 1]
            btns.append(btn)
        btns = sorted(btns, key=lambda x: btn_names.index(x))
        new_hotkey_str = "{}_".format(hotkeylist[0])
        for btn in btns:
            new_hotkey_str += "press_"
            new_hotkey_str += "{}_".format(btn)
        new_hotkey_str += "{}_{}".format(hotkeylist[-2], hotkeylist[-1])
        return new_hotkey_str


def hotkey_tabs(conf_window: ConfigWindow) -> None:
    q_tab = conf_window.add_tab("Question Hotkeys")
    q_manager = HotkeyTabManager(q_tab, "q")
    a_tab = conf_window.add_tab("Answer Hotkeys")
    a_manager = HotkeyTabManager(a_tab, "a")
    conf_window.widget_updates.append(q_manager.on_update)
    conf_window.widget_updates.append(a_manager.on_update)

    def save_hotkeys() -> None:
        hotkeys: Dict[str, str] = {}
        q_manager.get_data(hotkeys)
        a_manager.get_data(hotkeys)
        conf_window.conf.set("shortcuts", hotkeys)

    conf_window.execute_on_save(save_hotkeys)


def on_window_open(conf_window: ConfigWindow) -> None:
    conf_window.execute_on_close(refresh_config)


conf = ConfigManager()
conf.use_custom_window()
conf.on_window_open(on_window_open)
conf.add_config_tab(general_tab)
conf.add_config_tab(hotkey_tabs)
