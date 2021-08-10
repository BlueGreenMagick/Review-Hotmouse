from aqt import mw
from aqt.utils import tooltip


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
