window.inst_ws = new WebSocket("ws://127.0.0.1:5001/");
window.call_ws = new WebSocket("ws://127.0.0.1:5002/");
window.markup_sum = 0;
window.suspended = [];
window.load_state = false;

inst_ws.onopen = function () {
    inst_ws.send("readyFlag");
};

call_ws.onopen = function () {
    call_ws.send("readyFlag");
};

inst_ws.onmessage = function (event) {
    let json = JSON.parse(event.data);
    try {
        switch (json.type) {
            case ("eval"):
                call_ws.send(JSON.stringify({type: "return", value: eval(json.value), pid: json.pid}));
                break;
            case ("closeInst"):
                inst_ws.close();
                break;
            case ("closeCall"):
                call_ws.close();
                break;
            case ("closeBoth"):
                inst_ws.close();
                call_ws.close();
                break;
        }
    } catch (e) {
        call_ws.send(JSON.stringify({type: "error", value: e.toString(), pid: json.pid}));
    }
    inst_ws.send("finishFlag");
};

function call_bound_event(value) {
    call_ws.send(JSON.stringify({type: "bound_event", value: value}));
}

function bind_event(selector, event_type, value) {
    function func() {
        $(selector)[0][event_type] = function () {
            call_bound_event(value);
        }
    }
    if (load_state) {
        func()
    } else {
        suspended.push(func);
    }
}

function bind_events(selector, event_type, value) {
    function func() {
        $(selector).each(function () {
            $(this)[0][event_type] = function () {
                call_bound_event(value)
            }
        })
    }
    if (load_state) {
        func()
    } else {
        suspended.push(func);
    }
}

function unbind_event(selector, event_type) {
    function func() {
        $(selector)[0][event_type] = null
    }
    if (load_state) {
        func()
    } else {
        suspended.push(func);
    }
}

function unbind_events(selector, event_type) {
    function func() {
        $(selector).each(function () {
            $(this)[0][event_type] = null
        })
    }
    if (load_state) {
        func()
    } else {
        suspended.push(func);
    }
}

function call_event(selector, event_type) {
    $(selector)[0][event_type]()
}

function call_events(selector, event_type) {
    $(selector).each(function () {
        $(this)[0][event_type]()
    })
}

function get_inner_text(selector) {
    return $(selector)[0].innerText
}

function set_inner_text(selector, value) {
    $(selector)[0].innerText = value;
}

function get_inner_html(selector) {
    return $(selector)[0].innerHTML
}

function set_inner_html(selector, value) {
    $(selector)[0].innerHTML = value;
}

function get_value(selector) {
    return $(selector)[0].value
}

function set_value(selector, value) {
    $(selector)[0].value = value;
}

function get_css(selector, attr) {
    return $(selector).css(attr);
}

function set_css(selector, attr, value) {
    $(selector).css(attr, value);
}

function get_attr(selector, attr) {
    return $(selector).attr(attr);
}

function set_attr(selector, attr, value) {
    $(selector).attr(attr, value);
}

function get_prop(selector, attr) {
    return $(selector).prop(attr);
}

function set_prop(selector, attr, value) {
    $(selector).prop(attr, value);
}

function get_width(selector) {
    return $(selector).width()
}

function set_width(selector, value) {
    $(selector).width(value)
}

function get_height(selector) {
    return $(selector).height()
}

function set_height(selector, value) {
    $(selector).height(value)
}

function children(selector) {
    let ret = [];
    $(selector).children().each(function () {
        let class_ = `py-query-${markup_sum++}`
        $(this).addClass(class_);
        ret.push(`.${class_}`);
    });
    return ret
}

function find(selector1, selector2) {
    let ret = [];
    $(selector1).find(selector2).each(function () {
        let class_ = `py-query-${markup_sum++}`
        $(this).addClass(class_);
        ret.push(`.${class_}`);
    });
    return ret
}

function parent(selector) {
    let class_ = `py-query-${markup_sum++}`
    $(selector).parent().addClass(class_);
    return `.${class_}`
}

function parents(selector1, selector2) {
    let ret = [];
    $(selector1).parents(selector2).each(function () {
        let class_ = `py-query-${markup_sum++}`
        $(this).addClass(class_);
        ret.push(`.${class_}`);
    });
    return ret
}

function siblings(selector) {
    let ret = [];
    $(selector).siblings().each(function () {
        let class_ = `py-query-${markup_sum++}`
        $(this).addClass(class_);
        ret.push(`.${class_}`);
    });
    return ret
}

window.onload = function () {
    load_state = true;
    for (func of suspended) {
        func();
    }
}
