# Review Hotmouse

This is an Anki addon, that lets you review with a mouse. (No more keyboards)

## What is a hotmouse?

Probably a non-existant word, it means hotkey of a mouse instead of a keyboard. 'hotmouse' = 'hotkey' - 'key' + 'mouse'. 

## How to use

A hotmouse only works when in review mode. You can set different hotmouses for frontside and backside of a card.

By default, the hotmouses are configured as below:

right click: undo \
scroll down (front): show answer \
scroll up (back): again \
scroll down (back): good \
middle button + scroll up (back): hard \
middle button + scroll down (back): easy \
left click + right click (left click first): disable hotkey

When disabled, right click and the button 'enable hotmouse' pops out.

## Customizations

You can customize all hotmouses and its linked actions in the config. There are 200+ possible hotmouses combinations, and you can set 20 different actions for each hotmouse. More informations are provided in the addon config window. It can recognize 5 mouse buttons. (Please contact me if your mouse have more than 5 buttons, excluding the dpi button)

#### Example

`"q_press_left_click_right": "off"` : activates upon pressing right button(`click_right`), if on front side(`q`) and left button is pressed. (`press_left`) \
`"a_press_middle_press_xbutton1_wheel_down": "hard"` : activates upon scrolling the wheel downward(`wheel_down`), if on back side(`a`), xbutton1 button is pressed(`press_xbutton1`), and middle button is pressed(`press_middle`)
