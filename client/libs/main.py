import json
import socket
from .base import *
from .req import *
from .resp import *
from .config import config
from .ui import UI
import subprocess
import logging
import re
from threading import Thread
from itertools import cycle
from time import sleep
import sys

# logger config


# record the context of global data
gContext = {
    "playerID": None,
    "characterID": ["a12sdq2"],
    "gameOverFlag": False,
    "prompt": (
        "Take actions!\n"
        "'s': move in current direction\n"
        "'w': turn up\n"
        "'e': turn up right\n"
        "'d': turn down right\n"
        "'x': turn down\n"
        "'z': turn down left\n"
        "'a': turn up left\n"
        "'u': sneak\n"
        "'i': unsneak\n"
        "'j': master weapon attack\n"
        "'k': slave weapon attack\n"
        "Please complete all actions within one frame! \n"
        "[example]: a12sdq2\n"
    ),
    "steps": ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"],
    "gameBeginFlag": False,
}







def main():
    ui = UI()

    with Client() as client:
        client.connect()

        initPacket = PacketReq(PacketType.InitReq, cliGetInitReq())
        client.send(initPacket)
        print(gContext["prompt"])

        # IO thread to display UI
        t = Thread(target=recvAndRefresh, args=(ui, client))
        t.start()

        for c in cycle(gContext["steps"]):
            if gContext["gameBeginFlag"]:
                break
            print(
                f"\r\033[0;32m{c}\033[0m \33[1mWaiting for the other player to connect...\033[0m",
                flush=True,
                end="",
            )
            sleep(0.1)

        # IO thread accepts user input and sends requests
        while not gContext["gameOverFlag"]:
            if gContext["characterID"] is None:
                continue
            if action := cliGetActionReq(gContext["characterID"]):
                actionPacket = PacketReq(PacketType.ActionReq, action)
                client.send(actionPacket)

        # gracefully shutdown
        t.join()


if __name__ == "__main__":
    main()
