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

config = mw.addonManager.getConfig(__name__)


def refresh_config() -> None:
    global config
    config = mw.addonManager.getConfig(__name__)


def turn_on() -> None:
    if not manager.enabled:
        manager.enabled = True
        tooltip("Enabled hotmouse")


def turn_off() -> None:
    if manager.enabled:
        manager.enabled = False
        tooltip("Disabled hotmouse")


def toggle_on_off() -> None:
    if manager.enabled:
        manager.enabled = False
        tooltip("Disabled hotmouse")
    else:
        manager.enabled = True
        tooltip("Enabled hotmouse")


def answer_hard() -> None:
    cnt = mw.col.sched.answerButtons(mw.reviewer.card)
    if cnt == 4:
        mw.reviewer._answerCard(2)


def answer_good() -> None:
    cnt = mw.col.sched.answerButtons(mw.reviewer.card)
    if cnt == 2:
        mw.reviewer._answerCard(2)
    elif cnt == 3:
        mw.reviewer._answerCard(2)
    elif cnt == 4:
        mw.reviewer._answerCard(3)


def answer_easy() -> None:
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
    "undo": mw.onUndo,
    "show_ans": mw.reviewer._getTypedAnswer,
    "again": lambda: mw.reviewer._answerCard(1),
    "hard": answer_hard,
    "good": answer_good,
    "easy": answer_easy,
    "delete": mw.reviewer.onDelete,
    "suspend_card": mw.reviewer.onSuspendCard,
    "suspend_note": mw.reviewer.onSuspend,
    "bury_card": mw.reviewer.onBuryCard,
    "bury_note": mw.reviewer.onBuryNote,
    "mark": mw.reviewer.onMark,
    "red": lambda: mw.reviewer.setFlag(1),
    "orange": lambda: mw.reviewer.setFlag(2),
    "green": lambda: mw.reviewer.setFlag(3),
    "blue": lambda: mw.reviewer.setFlag(4),
    "audio": mw.reviewer.replayAudio,
    "record_voice": mw.reviewer.onRecordVoice,
    "replay_voice": mw.reviewer.onReplayRecorded,
}
ACTION_OPTS = list(ACTIONS.keys())


class Button(Enum):
    left = Qt.LeftButton
    right = Qt.RightButton
    middle = Qt.MiddleButton
    xbutton1 = Qt.XButton1
    xbutton2 = Qt.XButton2


class WheelDir(Enum):
    DOWN = -1
    UP = 1

    @classmethod
    def from_delta(cls, delta: Union[int, float]) -> Optional["WheelDir"]:
        if delta > 0:
            return cls.UP
        elif delta < 0:
            return cls.DOWN
        else:
            return None


class HotmouseManager:
    def __init__(self) -> None:
        self.enabled = True
        self.last_scroll_time = datetime.datetime.now()

    @staticmethod
    def get_pressed_buttons(qbuttons: Qt.MouseButtons) -> List[Button]:
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

    def execute_shortcut(self, hotkey_str: str) -> None:
        if self.enabled and config["z_debug"]:
            tooltip(hotkey_str)
        shortcuts = config["shortcuts"]
        if hotkey_str in shortcuts:
            action_str = shortcuts[hotkey_str]
            if not self.enabled and action_str not in ("on", "on_off"):
                return
            if config["tooltip"]:
                tooltip(action_str)
            ACTIONS[action_str]()

    def on_mouse_press(self, event: QMouseEvent) -> None:
        btns = self.get_pressed_buttons(event.buttons())
        btn = event.button()
        try:
            pressed = Button(event.button())
            btns.remove(pressed)
        except ValueError:  # Ignore unknown button
            print(f"Review Hotmouse: Unknown Button Pressed: {btn}")
            return
        hotkey_str = self.build_hotkey(btns, click=pressed)
        self.execute_shortcut(hotkey_str)

    def on_mouse_scroll(self, event: QWheelEvent) -> None:
        angle_delta = event.angleDelta().y()
        wheel_dir = WheelDir.from_delta(angle_delta)
        self.handle_scroll(wheel_dir, event.buttons())

    def handle_scroll(self, wheel_dir: WheelDir, qbtns: Qt.MouseButtons) -> None:
        curr_time = datetime.datetime.now()
        time_diff = curr_time - self.last_scroll_time
        self.last_scroll_time = curr_time
        if time_diff.total_seconds() * 1000 > config["threshold_wheel_ms"]:
            btns = self.get_pressed_buttons(qbtns)
            hotkey_str = self.build_hotkey(btns, wheel=wheel_dir)
            self.execute_shortcut(hotkey_str)


# MousePress and MouseRelease events on QWebEngineView is not triggered, only on its child widgets.
@no_type_check
def event_filter(
    target: AnkiWebView,
    obj: QObject,
    event: QEvent,
    _old: Callable = lambda t, o, e: False,
) -> bool:
    if mw.state == "review":
        if event.type() == QEvent.MouseButtonPress:
            # TODO: Check if pressed on the scroll bar
            manager.on_mouse_press(event)
            return True
        elif event.type() == QEvent.Wheel:
            manager.on_mouse_scroll(event)
            return True
    return _old(target, obj, event)


def on_child_event(target: AnkiWebView, event: QChildEvent) -> None:
    if event.added():
        add_event_filter(event.child(), target)


def on_context_menu(
    target: QWebEngineView,
    ev: QContextMenuEvent,
    _old: Callable = lambda t, e: None,
) -> None:
    if manager.enabled and mw.state == "review":
        return
    _old(target, ev)


@no_type_check
def installFilters() -> None:
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


def add_event_filter(object: QObject, master: AnkiWebView) -> None:
    """Add event filter to the widget and its children, to master"""
    object.installEventFilter(master)
    child_object = object.children()
    for w in child_object:
        add_event_filter(w, master)


def on_window_open() -> None:
    installFilters()
    for target in [mw.web, mw.bottomWeb, mw.toolbarWeb]:
        add_event_filter(target, target)


def addTurnonAddon(wv: AnkiWebView, m: QMenu) -> None:
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
    """Receive pycmd message."""
    if not isinstance(context, aqt.reviewer.Reviewer):
        return handled
    addon_key = "ReviewHotmouse#"
    if not message.startswith(addon_key):
        return handled

    req = json.loads(message[len(addon_key) :])  # type: Dict[str, Any]
    if req["key"] == "wheel":
        wheel_delta = req["value"]  # type: int
        wheel_dir = WheelDir.from_delta(wheel_delta)
        qbtns = mw.app.mouseButtons()
        manager.handle_scroll(wheel_dir, qbtns)
        return (True, True)

    return handled


manager = HotmouseManager()

gui_hooks.main_window_did_init.append(on_window_open)
gui_hooks.webview_will_show_context_menu.append(addTurnonAddon)
gui_hooks.webview_will_set_content.append(inject_web_content)
gui_hooks.webview_did_receive_js_message.append(handle_js_message)
mw.addonManager.setWebExports(__name__, r"web/.*(css|js)")
