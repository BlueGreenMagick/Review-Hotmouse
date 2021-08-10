import datetime

from aqt import mw
from aqt.qt import QEvent, Qt
from aqt.webview import AnkiWebView
from anki.hooks import addHook, wrap
from aqt.utils import tooltip

from . import actions

config = mw.addonManager.getConfig(__name__)
ON = True
ignore_release = False


ACTIONS = {
    "<none>": lambda: None,
    "": lambda: None,
    "off": actions.turn_off,
    "undo": mw.onUndo,
    "show_ans": mw.reviewer._getTypedAnswer,
    "again": lambda: mw.reviewer._answerCard(1),
    "hard": actions.answer_hard,
    "good": actions.answer_good,
    "easy": actions.answer_easy,
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
    "context_menu": lambda x="hotmouse_review": mw.web.contextMenuEvent(x),
}

BUTTONS = {
    "left": Qt.LeftButton,
    "right": Qt.RightButton,
    "middle": Qt.MiddleButton,
    "xbutton1": Qt.XButton1,
    "xbutton2": Qt.XButton2,
    "xbutton3": Qt.ExtraButton3,
    "xbutton4": Qt.ExtraButton4,
    "xbutton5": Qt.ExtraButton5,
    "xbutton6": Qt.ExtraButton6,
    "xbutton7": Qt.ExtraButton7,
    "xbutton8": Qt.ExtraButton8,
    "xbutton9": Qt.ExtraButton9,
}

BUTTONS_INVERSE = {v: k for k, v in BUTTONS.items()}


def get_pressed_buttons(qbuttons, btn=None):
    buttons = []
    for b in BUTTONS:
        if qbuttons & BUTTONS[b]:
            buttons.append(b)
        elif btn and btn == BUTTONS[b]:
            buttons.append(b)
    return buttons


def mouse_shortcut(btns, wheel=0, click=None):
    # build shortcut string
    if mw.reviewer.state == "question":
        shortcut_key_str = "q_"
    elif mw.reviewer.state == "answer":
        shortcut_key_str = "a_"
    for btn in btns:
        shortcut_key_str += "press_{}_".format(btn)
    if click:
        shortcut_key_str += "click_{}_".format(click)
    if wheel == 1:
        shortcut_key_str += "wheel_up_"
    elif wheel == -1:
        shortcut_key_str += "wheel_down_"
    shortcut_key_str = shortcut_key_str[:-1]  # removes '_' at the end
    if config["z_debug"]:
        tooltip(shortcut_key_str)

    # check if shortcut exist, run designated action if it does
    if shortcut_key_str in config:
        action_str = config[shortcut_key_str]
        ACTIONS[action_str]()
        if config["tooltip"]:
            tooltip(action_str)


def on_mouse_press(event):  # click
    btns = get_pressed_buttons(event.buttons())
    pressed = BUTTONS_INVERSE[event.button()]
    btns.remove(pressed)
    if len(btns) == 0:
        ignore_release = False  # because sometimes it is not set to True on release
    mouse_shortcut(btns, click=pressed)
    return


def on_mouse_release(event):  # press
    global ignore_release
    btns = event.buttons()
    btn = event.button()
    btns = get_pressed_buttons(btns, btn)
    if ignore_release == False:
        mouse_shortcut(btns)
        ignore_release = True
    if len(btns) == 1:  # released all mouse buttons
        ignore_release = False
    return


def on_mouse_scroll(event):
    global last_scroll_time, ignore_release
    curr_time = datetime.datetime.now()
    time_diff = curr_time - last_scroll_time
    if time_diff.total_seconds() * 1000 > config["threshold_wheel_ms"]:
        qbtns = event.buttons()
        btns = get_pressed_buttons(qbtns)
        angle_delta = event.angleDelta().y()
        if angle_delta > 0:
            mouse_shortcut(btns, 1)
        elif angle_delta < 0:
            mouse_shortcut(btns, -1)
    last_scroll_time = curr_time
    ignore_release = True


# Because MousePress and MouseRelease events on QWebEngineView is not triggered, only on its child widgets.
def on_child_event(self, event, _old=lambda s, e: None):
    if event.added():
        event.child().installEventFilter(self)
    return _old(self, event)


def event_filter(self, obj, event, _old=lambda s, o, e: None):
    if during_review(self):
        if event.type() == QEvent.MouseButtonPress:
            on_mouse_press(event)
        elif event.type() == QEvent.MouseButtonRelease:
            on_mouse_release(event)
        elif event.type() == QEvent.Wheel:
            on_mouse_scroll(event)
    return _old(self, obj, event)


def add_event_filter_children(obj):
    child_widgets = obj.children()
    for w in child_widgets:
        w.installEventFilter(mw.web)
        add_event_filter_children(w)


def new_contextMenuEvent(self, i, _old):
    if during_review(self) and i != "hotmouse_review":
        return
    else:
        _old(self, i)


def addTurnonAddon(self, m):
    if during_review(self, on=False):
        a = m.addAction("Enable Hotmouse")
        a.triggered.connect(actions.turn_on)


def during_review(wv, on=True):
    "on=False is passed when checking if in review but review hotmouse is turned off"
    if mw.state != "review":
        return False
    if ON != on:
        return False
    if wv not in [mw.web, mw.bottomWeb]:
        return False
    return True


def installFilters():
    try:
        AnkiWebView.eventFilter = wrap(
            AnkiWebView.eventFilter, event_filter, "around")
    except TypeError:
        AnkiWebView.eventFilter = event_filter
    try:
        AnkiWebView.childEvent = wrap(
            AnkiWebView.childEvent, on_child_event, "around")
    except TypeError:
        AnkiWebView.childEvent = on_child_event
    AnkiWebView.contextMenuEvent = wrap(
        AnkiWebView.contextMenuEvent, new_contextMenuEvent, "around"
    )
    add_event_filter_children(mw.web)


last_scroll_time = datetime.datetime.now()
addHook("AnkiWebView.contextMenuEvent", addTurnonAddon)
installFilters()
