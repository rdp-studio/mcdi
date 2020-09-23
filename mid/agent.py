import os
import pickle
import re
import threading
import time
from base64 import b64decode
import mido
import logging


class Server(object):
    def __init__(self, mc_server_path, midi_device, minmem=1024, maxmem=8192):
        if not os.path.exists(mc_server_path):
            raise ValueError("Minecraft server does not exist!")
        if not os.path.isfile(mc_server_path):
            raise ValueError("Minecraft server must be a file!")

        logging.debug(f"Initializing. Launching original server('{mc_server_path}') with pipe.")

        working_dir = os.path.split(mc_server_path)[0]

        if os.getcwd() != working_dir: os.chdir(working_dir)
        self.pipe = os.popen(f'java -jar -Xms{minmem}m -Xmx{maxmem}m "{mc_server_path}"')

        logging.debug(f"Connecting to MIDI output device('{midi_device}'). That may take a little time.")
        self.port = mido.open_output(midi_device)

        self.valid_info_count = 0
        self.inval_info_count = 0

    def handler(self, data):
        if matched := re.findall(r"\[\d{2}:\d{2}:\d{2}\sINFO\]:\s\[@\]\s!(.*)", data):
            message = pickle.loads(b64decode(matched[0]))
            time.sleep(message.time)
            self.port.send(message)

            self.valid_info_count += 1
        else:
            self.inval_info_count += 1

    def mainloop(self):
        logging.info(f"Minecraft server MIDI agent('{__file__}') started.")

        while data := self.pipe.readline():
            data = data.strip("\r\n\t\x20")

            thread = threading.Thread(
                target=self.handler, args=(data,)
            )
            thread.setDaemon(daemonic=True)
            thread.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    with Server(r"D:\Minecraft\Server\paper-243.jar", "VirtualMIDISynth #1 0") as server:
        server.mainloop()
