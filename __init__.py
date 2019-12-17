import datetime

from aqt import mw
from aqt.qt import QEvent, Qt
from aqt.webview import AnkiWebView
from anki.hooks import addHook, wrap
from aqt.utils import tooltip, showInfo

config = mw.addonManager.getConfig(__name__)

ACTIONS = { #need to seperate actions that only works in Answer side, and those that works in both question and answer
    "undo": mw.onUndo,
    "show_ans": mw.reviewer._getTypedAnswer,
    "again": lambda: mw.reviewer._answerCard(1),
    "hard": lambda: mw.reviewer._answerCard(2),
    "good": lambda: mw.reviewer._answerCard(3),
    "easy": lambda: mw.reviewer._answerCard(4),
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
    "<none>": lambda: None,
    "": lambda: None
}


BUTTONS = {
    "left": Qt.LeftButton,
    "right": Qt.RightButton,
    "middle": Qt.MiddleButton,
    "xbutton1": Qt.XButton1,
    "xbutton2": Qt.XButton2
}


last_scroll_time = datetime.datetime.now()
ignore_release = False

def get_pressed_buttons(qbuttons):
    buttons = []
    for b in BUTTONS:
        if qbuttons & BUTTONS[b]:
            buttons.append(b)
    return buttons

def mouse_shortcut(btns, wheel = 0):

    #build shortcut string
    if mw.reviewer.state == "question":
        shortcut_key_str = "q_"
    elif mw.reviewer.state == "answer":
        shortcut_key_str = "a_"
    for btn in btns:
        for b in BUTTONS:
            if b == btn:
                shortcut_key_str += "click_{}_".format(b)
                break
    if wheel == 1:
        shortcut_key_str += "wheel_up_"
    elif wheel == -1:
        shortcut_key_str += "wheel_down_"
    shortcut_key_str = shortcut_key_str[:-1] #removes '_' at the end
    tooltip(shortcut_key_str)

    #check if shortcut exist, run designated action if it does
    if shortcut_key_str in config:
        action_str = config[shortcut_key_str]
        ACTIONS[action_str]()

def on_mouse_press(event):
    return

def on_mouse_release(event):
    global ignore_release
    btns = get_pressed_buttons(event.buttons())
    if ignore_release == False:
        mouse_shortcut(btns)
        ignore_release = True
    if len(btns) == 0:
        ignore_release = False
    return

def on_mouse_scroll(event):
    global last_scroll_time
    if mw.state == "review":
        curr_time = datetime.datetime.now()
        time_diff = curr_time - last_scroll_time
        if time_diff.total_seconds()*1000 > config["threshold_wheel_ms"]:
            qbtns = event.buttons()
            btns = get_pressed_buttons(qbtns)
            angle_delta = event.angleDelta().y()
            if angle_delta > config["threshold_angle"]:
                mouse_shortcut(btns, 1)
            elif angle_delta < -1 * config["threshold_angle"]:
                mouse_shortcut(btns, -1)
        last_scroll_time = curr_time

#Because MousePress and MouseRelease events on QWebEngineView is not triggered, only on its child widgets. 
def on_child_event(self, event, _old=lambda s,e: None):
    tooltip("child")
    if event.added():
        event.child().installEventFilter(self)
    return _old(self, event)

def event_filter(self, obj, event, _old=lambda s,o,e: None):
    if mw.state == "review":
        if event.type() == QEvent.MouseButtonPress:
            on_mouse_press(event)
        elif event.type() == QEvent.MouseButtonRelease:
            on_mouse_release(event)
    return _old(self, obj, event)

def add_event_filter_children(obj):
    child_widgets = obj.children()
    for w in child_widgets:
        w.installEventFilter(mw.web)
        add_event_filter_children(w)


def on_wheel(self, event, _old=lambda s, e: None):
    on_mouse_scroll(event)
    return _old(self, event)


def onProfileLoaded():
    try:
        AnkiWebView.eventFilter = wrap(AnkiWebView.eventFilter, event_filter, "around")
    except TypeError:
        AnkiWebView.eventFilter = event_filter
    try:
        AnkiWebView.wheelEvent = wrap(AnkiWebView.wheelEvent, on_wheel, "around")
    except TypeError:
        AnkiWebView.wheelEvent = on_wheel
    try:
        AnkiWebView.childEvent = wrap(AnkiWebView.childEvent, on_child_event, "around")
    except TypeError:
        AnkiWebView.childEvent = on_child_event
    add_event_filter_children(mw.web)

addHook("profileLoaded", onProfileLoaded)
