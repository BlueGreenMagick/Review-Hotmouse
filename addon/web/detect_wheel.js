document.addEventListener("wheel", (ev) => {
    let req = {
        "key": "wheel",
        "value": ev.deltaY
    }
    let req_str = JSON.stringify(req)
    let resp = pycmd("ReviewHotmouse#" + req_str)
    if (resp) {
        ev.preventDefault()
        ev.stopPropagation()
    }
})


