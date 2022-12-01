from libs.req import *
from libs.base import *
from libs.resp import *
from libs.ui import UI
from libs.config import config
from threading import Thread
from itertools import cycle
from time import sleep
import sys
import socket
import re
import datetime

daytime = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
# logging.basicConfig(
#     # uncomment this will redirect log to file *client.log*
#     filename=f"client/logs/{daytime}.log",
#     format="[%(asctime)s][%(levelname)s] %(message)s",
#     filemode="a+",
# )
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
logger = None

int2action = {
        0: (ActionType.Move, EmptyActionParam()),
        1: (ActionType.TurnAround, TurnAroundActionParam(Direction.Above)),
        2: (ActionType.TurnAround, TurnAroundActionParam(Direction.TopRight)),
        3: (ActionType.TurnAround, TurnAroundActionParam(Direction.BottomRight)),
        4: (ActionType.TurnAround, TurnAroundActionParam(Direction.Bottom)),
        5: (ActionType.TurnAround, TurnAroundActionParam(Direction.BottomLeft)),
        6: (ActionType.TurnAround, TurnAroundActionParam(Direction.TopLeft)),
        7: (ActionType.Sneaky, EmptyActionParam()),
        8: (ActionType.UnSneaky, EmptyActionParam()),
        9: (ActionType.MasterWeaponAttack, EmptyActionParam()),
        10: (ActionType.SlaveWeaponAttack, EmptyActionParam()),
}



class Client(object):
    """Client obj that send/recv packet.

    Usage:
        >>> with Client() as client: # create a socket according to config file
        >>>     client.connect()     # connect to remote
        >>> 
    """
    def __init__(self) -> None:
        self.config = config
        self.host = self.config.get("Host")
        self.port = self.config.get("Port")
        assert self.host and self.port, "host and port must be provided"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def connect(self):
        self.config = config
        if self.socket.connect_ex((self.host, self.port)) == 0:
            print("connected")
        else:
            print(f"error in connecting to server {self.host}:{self.port}")
            exit(-1)
        return

    def send(self, req: PacketReq):
        msg = json.dumps(req, cls=JsonEncoder).encode("utf-8")
        length = len(msg)
        self.socket.sendall(length.to_bytes(8, sys.byteorder) + msg)
        # uncomment this will show req packet
        # logger.info(f"send PacketReq, content: {msg}")
        return

    def recv(self):
        length = int.from_bytes(self.socket.recv(8), sys.byteorder)
        bak_length = length
        result = b''
        while resp := self.socket.recv(length):
            result += resp
            length -= len(resp)
            if length <= 0:
                break
        return result
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.socket.close()
        if traceback:
            print(traceback)
            return False
        return True


def cliGetInitReq():
    """Get init request from user input."""
    masterWeaponType = input("Make choices!\nmaster weapon type: [select from {1-2}]: ")
    slaveWeaponType = input("slave weapon type: [select from {1-2}]: ")
    return InitReq(
        MasterWeaponType(int(masterWeaponType)), SlaveWeaponType(int(slaveWeaponType))
    )


def cliGetActionReq(characterID: int):
    """Get action request from user input.

    Args:
        characterID (int): Character's id that do actions.
    """

    def get_action(s: str):
        regex = r"[swedxzauijk]"
        matches = re.finditer(regex, s)
        for match in matches:
            yield match.group()

    str2action = {
        "s": (ActionType.Move, EmptyActionParam()),
        "w": (ActionType.TurnAround, TurnAroundActionParam(Direction.Above)),
        "e": (ActionType.TurnAround, TurnAroundActionParam(Direction.TopRight)),
        "d": (ActionType.TurnAround, TurnAroundActionParam(Direction.BottomRight)),
        "x": (ActionType.TurnAround, TurnAroundActionParam(Direction.Bottom)),
        "z": (ActionType.TurnAround, TurnAroundActionParam(Direction.BottomLeft)),
        "a": (ActionType.TurnAround, TurnAroundActionParam(Direction.TopLeft)),
        "u": (ActionType.Sneaky, EmptyActionParam()),
        "i": (ActionType.UnSneaky, EmptyActionParam()),
        "j": (ActionType.MasterWeaponAttack, EmptyActionParam()),
        "k": (ActionType.SlaveWeaponAttack, EmptyActionParam()),
    }

    actionReqs = []

    actions = input()

    for s in get_action(actions):
        actionReq = ActionReq(characterID, *str2action[s])
        actionReqs.append(actionReq)

    return actionReqs

def recvAndRefresh(ui: UI, client: Client, gContext):
    """Recv packet and refresh ui."""
    resp = client.recv()
    if ui is not None:
        refreshUI(ui, resp)
    
    if resp.type == PacketType.ActionResp:
        if len(resp.data.characters) and not gContext["gameBeginFlag"]:
            gContext["characterID"] = resp.data.characters[-1].characterID
            gContext["playerID"] = resp.data.playerID
            gContext["gameBeginFlag"] = True
        gContext["state"] = resp.data
        gContext["updateTime"] = gContext["updateTime"] + 1
    while resp.type != PacketType.GameOver:
        resp = client.recv()
        if ui is not None:
            refreshUI(ui, resp)
    if ui is not None:
        refreshUI(ui, resp)
    # print("Game Over")
    # logger.info(f"Game Over!")
    for (idx, score) in enumerate(resp.data.scores):
        if gContext["playerID"] == idx:
            print(f"You've got \33[1m{score} score\33[0m")
        else:
            print(f"The other player has got \33[1m{score} score \33[0m")
    if resp.data.result == ResultType.Win:
        print("\33[1mCongratulations! You win! \33[0m")
    elif resp.data.result == ResultType.Tie:
        print("\33[1mEvenly matched opponent \33[0m")
    elif resp.data.result == ResultType.Lose:
        print(
            "\33[1mThe goddess of victory is not on your side this time, but there is still a chance next time!\33[0m"
        )

    gContext["gameOverFlag"] = True
    print("Press any key to exit......")
    
def refreshUI(ui: UI, packet: PacketResp):
    """Refresh the UI according to the response."""
    data = packet.data
    if packet.type == PacketType.ActionResp:
        ui.playerID = data.playerID
        ui.color = data.color
        ui.characters = data.characters
        ui.score = data.score
        ui.kill = data.kill
        
        for block in data.map.blocks:
            if len(block.objs):
                ui.block = {
                    "x": block.x,
                    "y": block.y,
                    "color": block.color,
                    "valid": block.valid,
                    "obj": block.objs[-1].type,
                    "data": block.objs[-1].status,
                }
            else:
                ui.block = {
                    "x": block.x,
                    "y": block.y,
                    "color": block.color,
                    "valid": block.valid,
                    "obj": ObjType.Null,
                }
    ui.display()