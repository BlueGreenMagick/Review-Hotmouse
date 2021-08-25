**General Config**

- `tooltip`[true/false]: Show action when shortcut is triggered
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

**direction (wheel)**

- `up`
- `down`

**input types**

- `press` : Buttons being pressed when triggered.
- `click` : Trigger shortcut when this button is pressed.
- `wheel` : Scrolling inputs.

**Shortcut Syntax**:

- \[q/a\]\_\[click/wheel\]\_\[button/direction\]
- \[q/a\]\_\[press\]\_\[button\]\_\[click/wheel\]\_\[button/direction\]
- \[q/a\]_\[press\]\_\[button\]\_\[press\]\_\[button\]\_\[click/wheel\]\_\[button/direction\]
- etc.

When shortcut has multiple `press\_button`s, the buttons must be in the same order as listed under *mouse_buttons*.


**action**

- `<none>`: Does nothing
- `undo` 
- `off`
- `on`
- `on_off`
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
