from queue import Queue
from libs.ui import *
from api import Client, PacketReq, InitReq, refreshUI
import numpy as np
import json
from agent import MapAlgarithm
from libs.config import config, Config
import socket
import sys
class Env():
    needToAttack = {91:1, 10:1.2, 11:1}
    IDToCost = {
        9: 1,
        10: 1,
        11: 1,
        99: 99,
        98: 98,
        9: 1,
        91: 98,
    }
    mapIDMap = {
        'myBlock': 9,
        'otherBlock': 10,
        'enemyBlock': 11,
        'inValid': 99,
        'CDBuff': 9,
        'HPBuff': 9,
        'enemyWeapon': 98,
        'myWeapon': 9,
        'player': 98,
    }
    def __init__(self, masterWeapon, slaveWeapon, mapSize=16, startUI=True):
        self.client = Client() # 客户端
        self.client.connect() # 连接服务器
        self.ui = UI() if startUI else None
        self.mapSize = mapSize
        weaponChoose = PacketReq(PacketType.InitReq, InitReq(MasterWeaponType(int(masterWeapon)), SlaveWeaponType(int(slaveWeapon)))) # 选择武器
        # logger.info(f"weaponSelected master {masterWeapon} slave {slaveWeapon}")
        self.client.send(weaponChoose)
        
        # 玩家数据
        self.frame = None
        """
        playerID: 0, color: 🟥, characterNum: 1, character: 🦸‍️, score: 0, killNum: 0
        characterState: {"x": 7, "y": -1, "playerID": 0, "characterID": 0, "direction": 0,
        "color": 1, "hp": 100, "moveCD": 3, "moveCDLeft": 0, "isAlive": true, "isSneaky": false,
        "isGod": false, "rebornTimeLeft": 0, "godTimeLeft": 0,
        "slaveWeapon": {"weaponType": 1, "attackCD": 30, "attackCDLeft": 0},
        "masterWeapon": {"weaponType": 1, "attackCD": 3, "attackCDLeft": 0}}
        """
        self.hpBuff = []
        self.dangerPoint = []
        self.CDBuff = []
        self.otherBlocks = []
        self.characters = None
        self.ocharacters = {}
        self.playerID = None
        self.score = 0
        self.killNum = 0
        self.color = None
        self.direction = None
        self.otherBlockNum = 0
        self.distance = np.zeros((1,1))
        # 地图数据
        self.map = np.zeros((mapSize, mapSize), dtype=np.float32)
        self.result = 0
    def makeMap(self, map):
        """ -1-Brick 0-Other 1-MyColor 2-Buff1 3-Buff2 4-Weapon1 5-Weapon2 6-MyWeapon 7-MySelf 8-Opponent"""
        blocks = map['blocks']
        for block in blocks: # Keys: color frame objs x y valid
            x = block['x']
            y = -block['y']
            if not block['valid']:
                self.map[x,y] = self.mapIDMap['inValid']
            else:
                if 'objs' not in block.keys(): # 不是特殊物品
                    if self.color == block['color']:
                        self.map[x,y] = self.mapIDMap['myBlock']
                    elif block['color'] == 0:
                        self.map[x,y] = self.mapIDMap['otherBlock']
                        self.otherBlocks.append([x,-y])
                        self.otherBlockNum += 1
                    else:
                        self.map[x,y] = self.mapIDMap['enemyBlock']
                        self.otherBlocks.append([x,-y])
                        self.otherBlockNum += 1
                else:
                    objs = block['objs'][0]
                    if objs['type'] == 2: # 是buff物品
                        if objs['status']['buffType'] == 1: # MoveCD
                            self.map[x, y] = self.mapIDMap['CDBuff']
                            self.CDBuff.append([x,-y])
                        if objs['status']['buffType'] == 2: # HP
                            self.map[x, y] = self.mapIDMap['HPBuff']
                            self.hpBuff.append([x,-y])
                    elif objs['type'] == 3: # 是武器
                        if objs['status']['playerID'] != self.playerID:
                            self.map[x, y] = self.mapIDMap['enemyWeapon']
                        else:
                            self.map[x, y] = self.mapIDMap['myWeapon']
                    elif objs['type'] == 1: # 是玩家
                        if objs['status']['playerID'] == self.playerID:
                            self.map[x, y] = self.mapIDMap['player']
                        else:
                            self.ocharacters[objs['status']['playerID']] = objs['status']
                            if objs['status']['slaveWeapon']['attackCD'] - 1 == objs['status']['slaveWeapon']['attackCDLeft'] and [x, -y] not in self.dangerPoint:
                                MapAlgarithm.setDangerInRadius(self, [x,-y], 1)
                            else:
                                self.map[x, y] = self.mapIDMap['player']
                    else:
                        assert("No this obj type")
        for point in self.dangerPoint:
            self.map[point[0], -point[1]] = self.mapIDMap['enemyWeapon']
        self.ui.feedback = f"dangerPoint {self.dangerPoint}"
        for character in self.characters:
            for ocharacter, ocharacterState in self.ocharacters.items():
                my_x = character['x']
                my_y = character['y']
                enemy_x = ocharacterState['x']
                enemy_y = ocharacterState['y']
                self.distance[character['characterID']-1][ocharacterState['characterID']-1] = MapAlgarithm.calDistance(np.array([my_x, my_y]), np.array([enemy_x, enemy_y]))
    def writeResult(self):
        with open("result.out", "w") as file:
            file.write(str(self.score + self.killNum*10))
    def refresh(self):
        raw = self.client.recv()
        try:
            d = json.loads(raw)
        except:
            self.writeResult()
            self.client.socket.close()
            sys.exit()
        pakType = d.pop("type")
        data = d.pop("data")
        self.hpBuff = []
        self.CDBuff = []
        self.otherBlocks = []
        self.otherBlockNum = 0
        # pakType = int(resp['type']) # 1 InitReq 2 ActionReq 3 ActionResp 4 GameOver
        if pakType == 3:
            self.frame = int(data['frame'])
            self.color = int(data['color'])
            self.killNum = int(data['kill'])
            self.score = int(data['score'])
            self.playerID = int(data['playerID'])
            self.characters = data['characters']
            self.makeMap(data['map'])
        elif pakType == 4:
            self.writeResult()
            self.client.socket.close()
            sys.exit()
        if self.ui is not None:
            refreshUI(self.ui, PacketResp().from_json(raw))
        return True
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.client.__exit__(exc_type, exc_value, traceback)
        except:
            ...