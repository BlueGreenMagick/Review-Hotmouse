from typing import Any, Callable, List, Optional, Union, no_type_check
import datetime
from enum import Enum

from anki.hooks import wrap
from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import tooltip
from aqt.webview import AnkiWebView

config = mw.addonManager.getConfig(__name__)


def turn_on() -> None:
    if not manager.enabled:
        manager.enabled = True
        tooltip("Enabled hotmouse")


def turn_off() -> None:
    if manager.enabled:
        manager.enabled = False
        tooltip("Disabled hotmouse")


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
    "": lambda: None,
    "off": turn_off,
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


class Button(Enum):
    left = Qt.LeftButton
    right = Qt.RightButton
    middle = Qt.MiddleButton
    xbutton1 = Qt.XButton1
    xbutton2 = Qt.XButton2
    xbutton3 = Qt.ExtraButton3
    xbutton4 = Qt.ExtraButton4
    xbutton5 = Qt.ExtraButton5
    xbutton6 = Qt.ExtraButton6
    xbutton7 = Qt.ExtraButton7
    xbutton8 = Qt.ExtraButton8
    xbutton9 = Qt.ExtraButton9


class WheelDir(Enum):
    DOWN = -1
    UP = 1


class HotmouseManager():
    def __init__(self) -> None:
        self.enabled = True
        self.ready = True
        self.last_scroll_time = datetime.datetime.now()

    @staticmethod
    def get_pressed_buttons(event: Union[QMouseEvent, QWheelEvent]) -> List[Button]:
        """ Returns list of pressed button names, excluding the button that caused the trigger"""
        qbuttons = event.buttons()
        buttons = []
        for b in Button:
            if qbuttons & b.value:  # type: ignore
                buttons.append(b)
        return buttons

    def mouse_shortcut(self, btns: List[Button], wheel: Optional[WheelDir] = None, click: Optional[Button] = None) -> None:
        """wheel and click should not be passed an argument together!"""
        # build shortcut string
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
        if config["z_debug"]:
            tooltip(shortcut_key_str)

        # check if shortcut exist, run designated action if it does
        if shortcut_key_str in config:
            action_str = config[shortcut_key_str]
            ACTIONS[action_str]()
            if click:
                self.ready = False
            if config["tooltip"]:
                tooltip(action_str)

    def on_mouse_press(self, event: QMouseEvent) -> None:
        if not self.ready:
            return
        btns = self.get_pressed_buttons(event)
        btn = event.button()
        try:
            pressed = Button(event.button())
            btns.remove(pressed)
        except ValueError:  # Ignore unknown button
            print(f"Review Hotmouse: Unknown Button Pressed: {btn}")
            return
        self.mouse_shortcut(btns, click=pressed)

    def on_mouse_release(self, event: QMouseEvent) -> None:
        btns = self.get_pressed_buttons(event)
        if len(btns) == 1:  # released all mouse buttons
            self.ready = True

    def on_mouse_scroll(self, event: QWheelEvent) -> None:
        if not self.ready:
            return
        curr_time = datetime.datetime.now()
        time_diff = curr_time - self.last_scroll_time
        if time_diff.total_seconds() * 1000 > config["threshold_wheel_ms"]:
            btns = self.get_pressed_buttons(event)
            angle_delta = event.angleDelta().y()
            if angle_delta > 0:
                self.mouse_shortcut(btns, WheelDir.UP)
            elif angle_delta < 0:
                self.mouse_shortcut(btns, WheelDir.DOWN)
        self.last_scroll_time = curr_time


# MousePress and MouseRelease events on QWebEngineView is not triggered, only on its child widgets.
@no_type_check
def event_filter(target: AnkiWebView, obj: QObject, event: QEvent) -> Any:
    if mw.state == "review" and manager.enabled:
        if event.type() == QEvent.MouseButtonPress:
            manager.on_mouse_press(event)
        elif event.type() == QEvent.MouseButtonRelease:
            manager.on_mouse_release(event)
        elif event.type() == QEvent.Wheel:
            manager.on_mouse_scroll(event)


def on_child_event(target: QObject, event: QChildEvent) -> None:
    if event.added():
        event.child().installEventFilter(target)


def on_context_menu(target: QObject, ev: QContextMenuEvent, _old: Callable[[Any, Any], Any] = lambda t, e: None) -> None:
    if manager.enabled:
        return


@no_type_check
def installFilters() -> None:
    target = AnkiWebView
    if "eventFilter" in vars(target):
        target.eventFilter = wrap(
            target.eventFilter, event_filter, "before")
    else:
        target.eventFilter = event_filter
    if "childEvent" in vars(target):
        target.childEvent = wrap(target.childEvent, on_child_event, "before")
    else:
        target.childEvent = on_child_event
    if "contextMenuEvent" in vars(target):
        target.contextMenuEvent = wrap(
            target.contextMenuEvent, on_context_menu, "around")


def add_event_filter_children(parent: QObject, master: AnkiWebView) -> None:
    child_widgets = parent.children()
    for w in child_widgets:
        w.installEventFilter(master)
        add_event_filter_children(w, master)


def on_window_open() -> None:
    installFilters()
    for target in [mw.web, mw.bottomWeb, mw.toolbarWeb]:
        add_event_filter_children(target, target)


manager = HotmouseManager()


def addTurnonAddon(wv: AnkiWebView, m: QMenu) -> None:
    if mw.state == "review" and not manager.enabled:
        a = m.addAction("Enable Hotmouse")
        a.triggered.connect(turn_on)


gui_hooks.main_window_did_init.append(on_window_open)
gui_hooks.webview_will_show_context_menu.append(addTurnonAddon)
