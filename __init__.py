import datetime

from aqt import mw
from aqt.qt import QEvent, Qt
from aqt.webview import AnkiWebView
from anki.hooks import addHook, wrap
from aqt.utils import tooltip

config = mw.addonManager.getConfig(__name__)
ON = True
ignore_release = False

def turn_on():
    global ON
    if ON == False:
        ON = True
        tooltip("Enabled hotmouse")

def turn_off():
    global ON
    if ON == True:
        ON = False
        tooltip("Disabled hotmouse")

def answer_hard():
    cnt = mw.col.sched.answerButtons(mw.reviewer.card)
    if cnt == 4:
        mw.reviewer._answerCard(2)

def answer_good():
    cnt = mw.col.sched.answerButtons(mw.reviewer.card)
    if cnt == 2:
        mw.reviewer._answerCard(2)
    elif cnt == 3:
        mw.reviewer._answerCard(2)
    elif cnt == 4:
        mw.reviewer._answerCard(3)

def answer_easy():
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
    "context_menu": lambda x="hotmouse_review": mw.web.contextMenuEvent(x)
}

BUTTONS = {
    "left": Qt.LeftButton,
    "right": Qt.RightButton,
    "middle": Qt.MiddleButton,
    "xbutton1": Qt.XButton1,
    "xbutton2": Qt.XButton2
}

BUTTONS_INVERSE = {v: k for k, v in BUTTONS.items()}

def get_pressed_buttons(qbuttons, btn = None):
    buttons = []
    for b in BUTTONS:
        if qbuttons & BUTTONS[b]:
            buttons.append(b)
        elif btn and btn == BUTTONS[b]:
            buttons.append(b)
    return buttons

def mouse_shortcut(btns, wheel = 0, click=None):
    #build shortcut string
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
    shortcut_key_str = shortcut_key_str[:-1] #removes '_' at the end
    if config["z_debug"]:
        tooltip(shortcut_key_str)

    #check if shortcut exist, run designated action if it does
    if shortcut_key_str in config:
        action_str = config[shortcut_key_str]
        ACTIONS[action_str]()
        if(config["tooltip"]):
            tooltip(action_str)

def on_mouse_press(event): #click
    btns = get_pressed_buttons(event.buttons())
    pressed = BUTTONS_INVERSE[event.button()]
    btns.remove(pressed)
    if len(btns) == 0:
        ignore_release = False #because sometimes it is not set to True on release
    mouse_shortcut(btns, click=pressed)
    return

def on_mouse_release(event): #press
    global ignore_release
    btns = event.buttons() 
    btn = event.button()
    btns = get_pressed_buttons(btns, btn)
    if ignore_release == False:
        mouse_shortcut(btns)
        ignore_release = True
    if len(btns) == 1: #released all mouse buttons
        ignore_release = False
    return

def on_mouse_scroll(event):
    global last_scroll_time, ignore_release
    curr_time = datetime.datetime.now()
    time_diff = curr_time - last_scroll_time
    if time_diff.total_seconds()*1000 > config["threshold_wheel_ms"]:
        qbtns = event.buttons()
        btns = get_pressed_buttons(qbtns)
        angle_delta = event.angleDelta().y()
        if angle_delta > 0:
            mouse_shortcut(btns, 1)
        elif angle_delta < 0:
            mouse_shortcut(btns, -1)
    last_scroll_time = curr_time
    ignore_release = True

#Because MousePress and MouseRelease events on QWebEngineView is not triggered, only on its child widgets. 
def on_child_event(self, event, _old=lambda s,e: None):
    if event.added():
        event.child().installEventFilter(self)
    return _old(self, event)

def event_filter(self, obj, event, _old=lambda s,o,e: None):
    global ON
    if mw.state == "review" and ON == True:
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

#Doesn't seem to work anymore in newer anki
def on_wheel(self, event, _old=lambda s, e: None):
    global ON, ignore_release
    if mw.state == "review" and ON == True:
        ignore_release = True
        on_mouse_scroll(event)
    return _old(self, event)

def new_contextMenuEvent(self, i, _old):
    global ON
    if mw.state == "review" and ON == True and i != "hotmouse_review":
        return
    else:
        _old(self, i)

def addTurnonAddon(self, m):
    if mw.state == "review" and ON == False:
        a = m.addAction(_("Enable Hotmouse"))
        a.triggered.connect(turn_on)

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
    AnkiWebView.contextMenuEvent = wrap(AnkiWebView.contextMenuEvent, new_contextMenuEvent, "around")
    add_event_filter_children(mw.web)

last_scroll_time = datetime.datetime.now()
addHook("profileLoaded", onProfileLoaded)
addHook("AnkiWebView.contextMenuEvent", addTurnonAddon)