from typing import Any, Callable, List, Dict, Optional, Union, Tuple, no_type_check
from enum import Enum
import datetime
import json

from anki.hooks import wrap
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import tooltip
from aqt.webview import AnkiWebView, WebContent
import aqt


def WEBVIEW_TARGETS() -> List[AnkiWebView]:
    # Implemented as a function so attributes are resolved when called.
    # In case mw.web is reassigned to a different object
    return [mw.web, mw.bottomWeb]


config = mw.addonManager.getConfig(__name__)


def refresh_config() -> None:
    global config
    config = mw.addonManager.getConfig(__name__)


def turn_on() -> None:
    if not manager.enabled:
        manager.enable()
        tooltip("Enabled hotmouse")


def turn_off() -> None:
    if manager.enabled:
        manager.disable()
        tooltip("Disabled hotmouse")


def toggle_on_off() -> None:
    if manager.enabled:
        manager.disable()
        tooltip("Disabled hotmouse")
    else:
        manager.enable()
        tooltip("Enabled hotmouse")


def answer_again() -> None:
    if mw.reviewer.state == "question":
        mw.reviewer.state = "answer"
    mw.reviewer._answerCard(1)


def answer_hard() -> None:
    if mw.reviewer.state == "question":
        mw.reviewer.state = "answer"
    cnt = mw.col.sched.answerButtons(mw.reviewer.card)
    if cnt == 4:
        mw.reviewer._answerCard(2)


def answer_good() -> None:
    if mw.reviewer.state == "question":
        mw.reviewer.state = "answer"
    cnt = mw.col.sched.answerButtons(mw.reviewer.card)
    if cnt == 2:
        mw.reviewer._answerCard(2)
    elif cnt == 3:
        mw.reviewer._answerCard(2)
    elif cnt == 4:
        mw.reviewer._answerCard(3)


def answer_easy() -> None:
    if mw.reviewer.state == "question":
        mw.reviewer.state = "answer"
    cnt = mw.col.sched.answerButtons(mw.reviewer.card)
    if cnt == 3:
        mw.reviewer._answerCard(3)
    elif cnt == 4:
        mw.reviewer._answerCard(4)


ACTIONS = {
    "<none>": lambda: None,
    "on": turn_on,
    "off": turn_off,
    "on_off": toggle_on_off,
    "undo": lambda: mw.onUndo() if mw.form.actionUndo.isEnabled() else None,
    "show_ans": lambda: mw.reviewer._getTypedAnswer(),
    "again": answer_again,
    "hard": answer_hard,
    "good": answer_good,
    "easy": answer_easy,
    "delete": lambda: mw.reviewer.onDelete(),
    "suspend_card": lambda: mw.reviewer.onSuspendCard(),
    "suspend_note": lambda: mw.reviewer.onSuspend(),
    "bury_card": lambda: mw.reviewer.onBuryCard(),
    "bury_note": lambda: mw.reviewer.onBuryNote(),
    "mark": lambda: mw.reviewer.onMark(),
    "red": lambda: mw.reviewer.setFlag(1),
    "orange": lambda: mw.reviewer.setFlag(2),
    "green": lambda: mw.reviewer.setFlag(3),
    "blue": lambda: mw.reviewer.setFlag(4),
    "audio": lambda: mw.reviewer.replayAudio(),
    "record_voice": lambda: mw.reviewer.onRecordVoice(),
    "replay_voice": lambda: mw.reviewer.onReplayRecorded(),
}
ACTION_OPTS = list(ACTIONS.keys())


class Button(Enum):
    left = Qt.MouseButton.LeftButton
    right = Qt.MouseButton.RightButton
    middle = Qt.MouseButton.MiddleButton
    xbutton1 = Qt.MouseButton.XButton1
    xbutton2 = Qt.MouseButton.XButton2


class WheelDir(Enum):
    DOWN = -1
    UP = 1

    @classmethod
    def from_qt(cls, angle_delta: QPoint) -> Optional["WheelDir"]:
        delta = angle_delta.y()
        if delta > 0:
            return cls.UP
        elif delta < 0:
            return cls.DOWN
        else:
            return None

    @classmethod
    def from_web(cls, delta: int) -> Optional["WheelDir"]:
        """web and qt has opposite delta sign"""
        if delta < 0:
            return cls.UP
        elif delta > 0:
            return cls.DOWN
        else:
            return None


class HotmouseManager:
    def __init__(self) -> None:
        self.enabled = config["default_enabled"]
        self.last_scroll_time = datetime.datetime.now()
        self.add_menu()

    def add_menu(self) -> None:
        self.action = QAction("Enable/Disable Review Hotmouse", mw)
        self.action.triggered.connect(toggle_on_off)
        mw.form.menuTools.addAction(self.action)
        self.update_menu()

    def update_menu(self) -> None:
        if self.enabled:
            label = "Disable Review Hotmouse"
        else:
            label = "Enable Review Hotmouse"
        self.action.setText(label)

    def enable(self) -> None:
        self.enabled = True
        self.update_menu()

    def disable(self) -> None:
        self.enabled = False
        self.update_menu()

    @staticmethod
    def get_pressed_buttons(qbuttons: "Qt.MouseButtons") -> List[Button]:
        """Returns list of pressed button names, excluding the button that caused the trigger"""
        buttons = []
        for b in Button:
            if qbuttons & b.value:  # type: ignore
                buttons.append(b)
        return buttons

    @staticmethod
    def build_hotkey(
        btns: List[Button],
        wheel: Optional[WheelDir] = None,
        click: Optional[Button] = None,
    ) -> str:
        """One and only one of wheel or click must be passed as an argument."""
        if mw.reviewer.state == "question":
            shortcut_key_str = "q"
        elif mw.reviewer.state == "answer":
            shortcut_key_str = "a"
        for btn in btns:
            shortcut_key_str += "_press_{}".format(btn.name)
        if click:
            shortcut_key_str += "_click_{}".format(click.name)
        if wheel == WheelDir.UP:
            shortcut_key_str += "_wheel_up"
        elif wheel == WheelDir.DOWN:
            shortcut_key_str += "_wheel_down"
        return shortcut_key_str

    def execute_shortcut(self, hotkey_str: str) -> bool:
        """Returns True if shortcut exists and is executed."""
        if self.enabled and config["z_debug"]:
            tooltip(hotkey_str)
        shortcuts = config["shortcuts"]
        if hotkey_str in shortcuts:
            action_str = shortcuts[hotkey_str]
        else:
            action_str = ""

        if not self.enabled and action_str not in ("on", "on_off"):
            return False
        if not action_str:
            return False
        if config["tooltip"]:
            tooltip(action_str)
        ACTIONS[action_str]()
        return True

    def on_mouse_press(self, event: QMouseEvent) -> bool:
        """Returns True if shortcut is executed"""
        btns = self.get_pressed_buttons(event.buttons())
        btn = event.button()
        try:
            pressed = Button(event.button())
            btns.remove(pressed)
        except ValueError:  # Ignore unknown button
            print(f"Review Hotmouse: Unknown Button Pressed: {btn}")
            return False
        hotkey_str = self.build_hotkey(btns, click=pressed)
        return self.execute_shortcut(hotkey_str)

    def on_mouse_scroll(self, event: QWheelEvent) -> bool:
        """Returns True if shortcut is executed"""
        wheel_dir = WheelDir.from_qt(event.angleDelta())
        if wheel_dir is None:
            return False
        return self.handle_scroll(wheel_dir, event.buttons())

    def handle_scroll(self, wheel_dir: WheelDir, qbtns: "Qt.MouseButtons") -> bool:
        """Returns True if shortcut is executed"""
        curr_time = datetime.datetime.now()
        time_diff = curr_time - self.last_scroll_time
        self.last_scroll_time = curr_time
        if time_diff.total_seconds() * 1000 > config["threshold_wheel_ms"]:
            btns = self.get_pressed_buttons(qbtns)
            hotkey_str = self.build_hotkey(btns, wheel=wheel_dir)
            return self.execute_shortcut(hotkey_str)
        else:
            return self.enabled


@no_type_check
def event_filter(
    target: AnkiWebView,
    obj: QObject,
    event: QEvent,
    _old: Callable = lambda t, o, e: False,
) -> bool:
    """Because Mouse events are triggered on QWebEngineView's child widgets.

    Event propagation is only stopped when shortcut is triggered.
    This is so clicking on answer buttons and selecting text works.
    And `left_click` shortcut should be discouraged because of above.
    """
    if target not in WEBVIEW_TARGETS():
        return _old(target, obj, event)
    if mw.state == "review":
        if event.type() == QEvent.Type.MouseButtonPress:
            if manager.on_mouse_press(event):
                return True
        elif event.type() == QEvent.Type.Wheel:
            if manager.on_mouse_scroll(event):
                return True
    return _old(target, obj, event)


def on_child_event(target: AnkiWebView, event: QChildEvent) -> None:
    if target not in WEBVIEW_TARGETS():
        return
    if event.added():
        add_event_filter(event.child(), target)


def on_context_menu(
    target: QWebEngineView,
    ev: QContextMenuEvent,
    _old: Callable = lambda t, e: None,
) -> None:
    if target not in WEBVIEW_TARGETS():
        _old(target, ev)
        return
    if manager.enabled and mw.state == "review":
        return None  # ignore event
    _old(target, ev)


@no_type_check
def install_filters() -> None:
    target = AnkiWebView
    if "eventFilter" in vars(target):
        target.eventFilter = wrap(target.eventFilter, event_filter, "around")
    else:
        target.eventFilter = event_filter
    if "childEvent" in vars(target):
        target.childEvent = wrap(target.childEvent, on_child_event, "before")
    else:
        target.childEvent = on_child_event
    if "contextMenuEvent" in vars(target):
        target.contextMenuEvent = wrap(
            target.contextMenuEvent, on_context_menu, "around"
        )
    else:
        target.contextMenuEvent = on_context_menu


def add_event_filter(object: QObject, master: AnkiWebView) -> None:
    """Add event filter to the widget and its children, to master"""
    object.installEventFilter(master)
    child_object = object.children()
    for w in child_object:
        add_event_filter(w, master)


def install_event_handlers() -> None:
    install_filters()
    for target in WEBVIEW_TARGETS():
        add_event_filter(target, target)


def add_context_menu_action(wv: AnkiWebView, m: QMenu) -> None:
    if mw.state == "review" and not manager.enabled:
        a = m.addAction("Enable Hotmouse")
        a.triggered.connect(turn_on)


def inject_web_content(web_content: WebContent, context: Optional[Any]) -> None:
    """Wheel events are not reliably detected with qt's event handler
    when the reviewer is scrollable. (For long cards)
    """
    if not isinstance(context, aqt.reviewer.Reviewer):
        return
    addon_package = mw.addonManager.addonFromModule(__name__)
    web_content.js.append(f"/_addons/{addon_package}/web/detect_wheel.js")


def handle_js_message(
    handled: Tuple[bool, Any], message: str, context: Any
) -> Tuple[bool, Any]:
    """Receive pycmd message. Returns (handled?, return_value)"""
    if not isinstance(context, aqt.reviewer.Reviewer):
        return handled
    addon_key = "ReviewHotmouse#"
    if not message.startswith(addon_key):
        return handled

    req = json.loads(message[len(addon_key) :])  # type: Dict[str, Any]
    if req["key"] == "wheel":
        wheel_delta = req["value"]  # type: int
        wheel_dir = WheelDir.from_web(wheel_delta)
        if wheel_dir is None:
            return (False, None)
        qbtns = mw.app.mouseButtons()
        executed = manager.handle_scroll(wheel_dir, qbtns)
        return (executed, executed)

    return handled


manager = HotmouseManager()

mw.addonManager.setWebExports(__name__, r"web/.*(css|js)")
gui_hooks.main_window_did_init.append(install_event_handlers)  # 2.1.28
gui_hooks.webview_will_show_context_menu.append(add_context_menu_action)  # 2.1.20
gui_hooks.webview_will_set_content.append(inject_web_content)  # 2.1.22
gui_hooks.webview_did_receive_js_message.append(handle_js_message)  # 2.1.20
