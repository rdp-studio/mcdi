import asyncio
import collections
import json
import logging
import multiprocessing
import os
import random
import sys
import threading
from typing import Any

import websockets
from PyQt5.QtCore import QUrl, QPoint, pyqtSignal, QSize
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QMainWindow, QApplication
from flask import Flask, render_template, render_template_string


def run_in_new_thread(*targets, thread_names=None):
    thread_list = []
    for i, target in enumerate(targets):
        thread = threading.Thread(target=target)
        thread.setDaemon(daemonic=True)
        if thread_names is not None:
            thread.setName(thread_names[i])
        thread.start()
        thread_list.append(thread)
    return thread_list


def run_in_new_process(*targets, process_names=None):
    process_list = []
    for i, target in enumerate(targets):
        process = multiprocessing.Process(target=target)
        process.daemon = True
        if process_names is not None:
            process.name = process_names[i]
        process.start()
        process_list.append(process)
    return process_list


def run_local_websocket(loop, port):
    start_server = websockets.serve(loop, '127.0.0.1', port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


class HtmlGuiWindow(QMainWindow):
    resize_signal = pyqtSignal(QSize)
    move_signal = pyqtSignal(QPoint)
    redirect_signal = pyqtSignal(str)

    def __init__(self, entrance, static_path="static", template_path="templates", *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.flask_app = Flask(__name__, static_folder=static_path, template_folder=template_path, root_path=".")
        self.stored_objects = []
        self.inst_ws: websockets.WebSocketServerProtocol = ...
        self.call_ws: websockets.WebSocketServerProtocol = ...
        self.inst_init_sig = threading.Event()
        self.call_init_sig = threading.Event()
        self.inst_queue_sig = threading.Event()
        self.inst_queue = collections.deque()
        self.call_queue_sig = threading.Event()
        self.call_queue = dict()

        @self.flask_app.route('/')
        def entrance_page():
            return render_template(entrance)

        for i in os.listdir(template_path):
            @self.flask_app.route(
                '/%s' % (t := os.path.splitext(i)[0]), endpoint=t
            )
            def template_page():
                return render_template(i)

        run_in_new_thread(
            self.flask_app.run,
            self.__inst_loop,
            self.__call_loop,
            thread_names=(
                "HTMG_FLASK_THREAD",
                "HTMG_INST_THREAD",
                "HTMG_CALL_THREAD"
            )
        )

        localpg_url = "http://127.0.0.1:5000/"
        self.webview = QWebEngineView()  # Initialize Chromium web engine
        self.webview.load(QUrl(localpg_url))
        self.webview.page().profile().clearHttpCache()  # No HTTP cache
        self.webview.setContextMenuPolicy(0)
        self.setCentralWidget(self.webview)

        self.resize_signal.connect(self._resize_slot)
        self.move_signal.connect(self._move_slot)
        self.redirect_signal.connect(self._redirect_slot)

    def _resize_slot(self, size):
        super().resize(size)

    def _move_slot(self, point):
        super().move(point)

    def _redirect_slot(self, localpg_url):
        self.webview.load(QUrl(localpg_url))
        self.webview.page().profile().clearHttpCache()  # No HTTP cache
        self.webview.setContextMenuPolicy(0)

    def resize(self, a0: QSize):
        self.resize_signal.emit(a0)

    def move(self, a0: QPoint) -> None:
        self.move_signal.emit(a0)

    def redirect_template(self, route):
        self.redirect_signal.emit(
            f"http://127.0.0.1:5000/{route}"
        )

    def redirect_cross_origin(self, url):
        self.redirect_signal.emit(url)

    def __inst_loop(self):
        self.inst_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.inst_loop)

        async def inst_loop(websocket: websockets.WebSocketServerProtocol, _):
            self.inst_ws = websocket  # Ready for external call
            self.inst_init_sig.set()  # Raise initialization flag

            while await websocket.recv() != "readyFlag":  # Wait for javascript
                logging.info("Invalid Javascript instruction ready flag!")
            logging.info("Javascript instruction websocket ready.")

            while True:  # Run self thing forever
                self.inst_queue_sig.wait()  # Wait for check lock

                while self.inst_queue:
                    queued_dict = self.inst_queue.popleft()  # Get queued item

                    await websocket.send(queued_dict["value"])  # Send value
                    while await websocket.recv() != "finishFlag":  # Wait for javascript
                        logging.info("Invalid Javascript instruction finish flag!")

                    queued_dict["sig"].set()  # Release execution lock

                self.inst_queue_sig.clear()  # Re-lock check lock

        run_local_websocket(inst_loop, 5001)

    def __call_loop(self):
        self.call_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.call_loop)

        async def call_loop(websocket: websockets.WebSocketServerProtocol, _):
            self.call_ws = websocket  # Ready for external call
            self.call_init_sig.set()  # Raise initialization flag

            while await websocket.recv() != "readyFlag":  # Wait for javascript
                logging.info("Invalid Javascript callback ready flag!")
            logging.info("Javascript callback websocket ready.")

            while True:  # Run self thing forever
                res = json.loads(await websocket.recv())

                if res["type"] == "bound_event":
                    run_in_new_thread(self.stored_objects[res["value"]])

                elif res["type"] == "return":
                    try:  # Try to match package ID
                        queued_dict = self.call_queue[res["pid"]]
                    except KeyError:  # No match
                        raise RuntimeError(f"Failed to match return PID: {res['pid']}.")

                    if "value" in res.keys() and queued_dict["block"]["ret"]:
                        queued_dict["value"] = res["value"]  # Receive value object

                    queued_dict["sig"].set()  # Release return lock

                elif res["type"] == "error":
                    try:  # Try to match package ID
                        queued_dict = self.call_queue[res["pid"]]
                    except KeyError:  # No match
                        raise RuntimeError(f"Failed to match error PID: {res['pid']}.")

                    if "value" in res.keys() and queued_dict["block"]["err"]:
                        queued_dict["value"] = res["value"]  # Receive error object

                    queued_dict["sig"].set()  # Release return lock

                await websocket.send("finishFlag")

        run_local_websocket(call_loop, 5002)

    def execute_js(self, code, pid=None, get_error=True, get_return=True) -> Any:
        if pid is None:  # PID not specified
            pid = random.randint(0, 2147483647)

        self.call_queue_sig.set()  # Release check lock
        self.call_queue[pid] = {
            "sig": (return_lock := threading.Event()), "value": None, "block": {"err": get_error, "ret": get_return},
        }  # Add return flag to queue

        self.inst_queue_sig.set()  # Release check lock
        self.inst_queue.append({
            "sig": (exec_lock := threading.Event()), "value": json.dumps({"type": "eval", "value": code, "pid": pid}),
        })  # Add call request to queue

        exec_lock.wait()  # Wait for execution lock
        return_lock.wait()  # Wait for return lock

        queue_item = self.call_queue.pop(pid)  # Clean-up

        return queue_item["value"]  # Return value

    def __call__(self, css_selector):
        return _LazyDOMElement(self, css_selector)


class _LazyDOMElement(object):
    __HTML_EVENTS = [
        "onblur", "onchange", "oncontextmenu", "onfocus", "oninput", "oninvalid", "onreset", "onselect", "onsubmit",
        "onkeydown", "onkeypress", "onkeyup", "onclick", "ondblclick", "ondrag", "ondragend", "ondragenter",
        "ondragleave", "ondragover", "ondragstart", "ondrop", "onmousedown", "onmousemove", "onmouseout", "onmouseover",
        "onmouseup", "onmousewheel", "onscroll", "onabort", "oncanplay", "oncanplaythrough", "ondurationchange",
        "onemptied", "onended", "onerror", "onloadeddata", "onloadstart", "onpause", "onplay", "onplaying",
        "onprogress", "onratechange", "onreadystatechange", "onseeked", "onseeking", "onstalled", "onsuspend",
        "ontimeupdate", "onvolumechange", "onwaiting", "onafterprint", "onbeforeprint", "onload", "onresize", "onunload"
    ]

    def __init__(self, window: HtmlGuiWindow, selector):
        self.__window: HtmlGuiWindow = window
        self.selector = selector

    @property
    def window(self):
        return self.__window

    @property
    def html_events(self):
        return self.__HTML_EVENTS

    def bind(self, event: str, function: callable, multiple=True, force=False) -> None:
        if event not in self.html_events and not force:
            raise ValueError(f"Unknown HTML event type: '{event}'. To dismiss self error, set argument force to True.")

        if not callable(function):
            raise TypeError(f"'{function.__class__.__name__}' object is not callable. Maybe you used a function call?")

        func_index = len(self.window.stored_objects)
        self.window.stored_objects.append(function)

        if multiple:
            run_in_new_thread(
                lambda: self.window.execute_js(f"bind_events('{self.selector}', '{event}', {func_index})"))
        else:
            run_in_new_thread(
                lambda: self.window.execute_js(f"bind_event('{self.selector}', '{event}', {func_index})"))

    def unbind(self, event: str, multiple=True, force=False) -> None:
        if event not in self.html_events and not force:
            raise ValueError(f"Unknown HTML event type: '{event}'. To dismiss self error, set argument force to True.")

        if multiple:
            run_in_new_thread(
                lambda: self.window.execute_js(f"unbind_events('{self.selector}', '{event}')"))
        else:
            run_in_new_thread(
                lambda: self.window.execute_js(f"unbind_event('{self.selector}', '{event}')"))

    def trigger(self, event: str, multiple=True, force=False) -> None:
        if event not in self.html_events and not force:
            raise ValueError(f"Unknown HTML event type: '{event}'. To dismiss self error, set argument force to True.")

        if multiple:
            run_in_new_thread(
                lambda: self.window.execute_js(f"call_events('{self.selector}', '{event}')"))
        else:
            run_in_new_thread(
                lambda: self.window.execute_js(f"call_event('{self.selector}', '{event}')"))

    def append(self, dom: str) -> None:
        self.inner_html = self.inner_html + dom

    def prepend(self, dom: str) -> None:
        self.inner_html = dom + self.inner_html

    def after(self, dom: str) -> None:
        self.window.execute_js(f"$('{self.selector}').after('{dom}')")

    def before(self, dom: str) -> None:
        self.window.execute_js(f"$('{self.selector}').before('{dom}')")

    def remove(self) -> None:
        self.window.execute_js(f"$('{self.selector}').remove()")

    def empty(self) -> None:
        self.window.execute_js(f"$('{self.selector}').empty()")

    def add_class(self, class_name: str) -> None:
        class_name = json.dumps(class_name)
        self.window.execute_js(f"$('{self.selector}').addClass({class_name})")

    def remove_class(self, class_name: str) -> None:
        class_name = json.dumps(class_name)
        self.window.execute_js(f"$('{self.selector}').removeClass({class_name})")

    def toggle_class(self, class_name: str) -> None:
        class_name = json.dumps(class_name)
        self.window.execute_js(f"$('{self.selector}').toggleClass({class_name})")

    def get_css(self, attribute: str) -> str:
        return self.window.execute_js(f"get_css('{self.selector}', '{attribute}')")

    def set_css(self, attribute: str, value) -> None:
        value = json.dumps(value)
        self.window.execute_js(f"set_css('{self.selector}', '{attribute}', {value})")

    def getattr(self, attribute: str) -> str:
        return self.window.execute_js(f"get_attr('{self.selector}', '{attribute}')")

    def setattr(self, attribute: str, value) -> None:
        value = json.dumps(value)
        self.window.execute_js(f"set_attr('{self.selector}', '{attribute}', {value})")

    def getprop(self, attribute: str) -> str:
        return self.window.execute_js(f"get_prop('{self.selector}', '{attribute}')")

    def setprop(self, attribute: str, value) -> None:
        value = json.dumps(value)
        self.window.execute_js(f"set_prop('{self.selector}', '{attribute}', {value})")

    def hide(self) -> None:
        self.window.execute_js(f"$('{self.selector}').hide()")

    def show(self) -> None:
        self.window.execute_js(f"$('{self.selector}').show()")

    def fade_in(self, speed="fast") -> None:
        self.window.execute_js(f"$('{self.selector}').fadeIn({json.dumps(speed)})")

    def fade_out(self, speed="fast") -> None:
        self.window.execute_js(f"$('{self.selector}').fadeOut({json.dumps(speed)})")

    def fade_to(self, opacity: float, speed="fast") -> None:
        self.window.execute_js(f"$('{self.selector}').fadeTo({json.dumps(speed)}, {opacity})")

    def fade_toggle(self, speed="fast") -> None:
        self.window.execute_js(f"$('{self.selector}').fadeToggle({json.dumps(speed)})")

    def slide_up(self, speed="fast") -> None:
        self.window.execute_js(f"$('{self.selector}').slideUp({json.dumps(speed)})")

    def slide_down(self, speed="fast") -> None:
        self.window.execute_js(f"$('{self.selector}').slideDown({json.dumps(speed)})")

    def slide_toggle(self, speed="fast") -> None:
        self.window.execute_js(f"$('{self.selector}').slideToggle({json.dumps(speed)})")

    def animate(self, css_set: dict, speed="fast") -> None:
        self.window.execute_js(f"$('{self.selector}').animate({json.dumps(css_set)}, {json.dumps(speed)})")

    @property
    def width(self) -> float:
        return self.window.execute_js(f"get_width('{self.selector}')")

    @width.setter
    def width(self, value) -> None:
        self.window.execute_js(f"set_width('{self.selector}', {value})")

    @property
    def height(self) -> float:
        return self.window.execute_js(f"get_height('{self.selector}')")

    @height.setter
    def height(self, value) -> None:
        self.window.execute_js(f"set_height('{self.selector}', {value})")

    @property
    def inner_text(self) -> str:
        return self.window.execute_js(f"get_inner_text('{self.selector}')")

    @inner_text.setter
    def inner_text(self, value: str) -> None:
        value = json.dumps(value)
        self.window.execute_js(f"set_inner_text('{self.selector}', {value})")

    @property
    def inner_html(self) -> str:
        return self.window.execute_js(f"get_inner_html('{self.selector}')")

    @inner_html.setter
    def inner_html(self, value: str) -> None:
        value = json.dumps(value)
        self.window.execute_js(f"set_inner_html('{self.selector}', {value})")

    @property
    def value(self) -> str:
        return self.window.execute_js(f"get_value('{self.selector}')")

    @value.setter
    def value(self, value: str) -> None:
        value = json.dumps(value)
        self.window.execute_js(f"set_value('{self.selector}', {value})")

    @property
    def children(self):
        for selector in self.window.execute_js(f"children('{self.selector}')"):
            yield self.window(selector)  # Creates a selector object

    def find(self, selector: str):
        for selector in self.window.execute_js(f"find('{self.selector}, '{selector}')"):
            yield self.window(selector)  # Creates a selector object

    @property
    def parent(self):
        return self.window(self.window.execute_js(f"parent('{self.selector}')"))

    def parents(self, selector: str):
        for selector in self.window.execute_js(f"parents('{self.selector}', '{selector}')"):
            yield self.window(selector)  # Creates a selector object

    @property
    def siblings(self):
        for selector in self.window.execute_js(f"siblings('{self.selector}')"):
            yield self.window(selector)  # Creates a selector object

    def __iter__(self):
        for selector in self.window.execute_js(f"each('{self.selector}')"):
            yield self.window(selector)  # Creates a selector object


class __ExampleWindow(HtmlGuiWindow):
    def __init__(self, *args, **kwargs):
        super().__init__("example.html", *args, **kwargs)
        self.setWindowTitle("HTMG Form Example")

        self("#id").bind("onclick", self.foo)

    def foo(self):
        self("#id").set_css(
            "background", f"rgb({random.randint(64, 255)}, {random.randint(64, 255)}, {random.randint(64, 255)})")


if __name__ == '__main__':
    application = QApplication(sys.argv)
    __ExampleWindow().show()  # A simple example
    application.exit(application.exec_())
