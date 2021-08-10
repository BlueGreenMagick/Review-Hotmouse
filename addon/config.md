**General Config**

- `tooltip`[true/false]: Show tooltip when hotmouse action is triggered
- `z_debug`[true/false]: Show hotkey on mouse action.

**Card side**

- `q` : Works when viewing question
- `a` : Works when viewing answers

**mouse buttons (press/click)**

- `left`
- `right`
- `middle`
- `xbutton1`
- `xbutton2`

**wheel**

- `up`
- `down`

**input types**

- `press` : Buttons being pressed when triggered. 'press' only hotmouse is triggered upon the first release of a button.
- `click` : Triggered when the button is pressed.
- `wheel` : Scrolling inputs.

**multi inputs**

When 2+ inputs are combined to make a shortcut, the order of input type must be press -> click -> wheel, and for multiple 'press', the order of mouse buttons. There can only be one 'click' and one 'wheel' maximum.

**action**

- `undo` 
- `off`
- `again`
- `hard`
- `good`
- `easy`
- `delete`
- `suspend_card`
- `suspend_note`
- `bury_card`
- `bury_note`
- `mark`
- `red`
- `orange`
- `green`
- `blue`
- `audio` : replay audio
- `record_voice`
- `replay_voice`
- `context_menu` : 'copy' context menu.
- `<none>`: Does nothing

**syntax**:

- \[q/a\]\_\[type\]\_\[button/wheel\]
- \[q/a\]\_\[type\]\_\[button\]\_\[type\]\_\[button/wheel\]
- \[q/a\]_\[type\]\_\[button\]\_\[type\]\_\[button\]\_\[type\]\_\[button/wheel\]

view examples at https://github.com/BlueGreenMagick/Hotmouse-Review