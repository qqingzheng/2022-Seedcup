from libs.req import *
import numpy as np
from queue import PriorityQueue
class ActionTree:
    def __init__(self):
        self.children = []
        self.buf = {}
        self.priorityQueue = PriorityQueue()
    def setBuf(self, key, value, force=False):
        self.buf[key] = value
    def saveBasicInfo(self, env, characterIdx):
        self.setBuf("myX", env.characters[characterIdx]['x'])
        self.setBuf("myY", env.characters[characterIdx]['y'])
        self.setBuf("enemyX", env.ocharacters[list(env.ocharacters.keys())[0]]['x'])
        self.setBuf("enemyY", env.ocharacters[list(env.ocharacters.keys())[0]]['y'])
        self.setBuf("move", False)
        self.setBuf("attack", False)
    def isPointDanger(self, point):
        if self.env.map[point[0], -point[1]] >= 90:
            return True
        else:
            return False
    def isPointValid(self, point):
        if point[0] >= 0 and point[0] < self.env.mapSize and -point[1] >= 0 and -point[1] < self.env.mapSize and self.env.map[point[0], -point[1]] != self.env.mapIDMap['inValid']:
            return True
        else:
            return False
    def addChild(self, node):
        self.children.append(node)
    def execute(self, env, characterIdx):
        self.env = env
        self.characterIdx = characterIdx
        self.saveBasicInfo(self.env, characterIdx)
        while not self.priorityQueue.empty():
            self.priorityQueue.get_nowait().execute(self)
        for child in self.children:
            child.execute(self)
class PrimitiveOpration:
    def MoveToPoint(root, myPoint, targetPoint, type='near', radius=1):
        if type == 'near':
            nearPoint = MapAlgarithm.getNearValidPoint(root, targetPoint, radius, exclude=myPoint)
            if nearPoint is not None:
                path = MapAlgarithm.AStarPathSearch(root.env, myPoint, nearPoint)
                if len(path) != 0:
                    direction = MapAlgarithm.getDirection(myPoint, path[-1])
                    if direction != -1:
                        PrimitiveOpration.Move(root, direction)
        else:
            path = MapAlgarithm.AStarPathSearch(root.env, myPoint, targetPoint)
            if len(path) != 0:
                direction = MapAlgarithm.getDirection(myPoint, path[-1])
                if direction != -1:
                    PrimitiveOpration.Move(root, direction)
        root.buf['move'] = True
    def AttackToPoint(root, myPoint, targetPoint):
        direction = MapAlgarithm.getDirection(myPoint, targetPoint)
        if direction != -1:
            PrimitiveOpration.Attack(root, direction)
        root.buf['attack'] = True
    def SlaveAttack(root, direction):
        env = root.env
        characterIdx = root.characterIdx
        currentDirection = env.characters[characterIdx]['direction']
        if currentDirection == direction:
            sendAction(root, [getAction(characterIdx, ActionType.SlaveWeaponAttack, EmptyActionParam())])
        else:
            sendAction(root, [getAction(characterIdx, ActionType.TurnAround, TurnAroundActionParam(direction)),
                                getAction(characterIdx, ActionType.SlaveWeaponAttack, EmptyActionParam())])
    def Attack(root, direction):
        env = root.env
        characterIdx = root.characterIdx
        currentDirection = env.characters[characterIdx]['direction']
        if len(root.env.dangerPoint) != 0:
            myX = root.buf['myX']
            myY = root.buf['myY']
            myPoint = np.array([myX, myY]) + 2*np.array(MapAlgarithm.nearPoint[direction])
            for near in MapAlgarithm.nearPoint:
                if list(myPoint) in root.env.dangerPoint:
                    root.env.dangerPoint.remove(list(myPoint))
                myPoint = myPoint + np.array(near) 
        if currentDirection == direction:
            sendAction(root, [getAction(characterIdx, ActionType.MasterWeaponAttack, EmptyActionParam())])
        else:
            sendAction(root, [getAction(characterIdx, ActionType.TurnAround, TurnAroundActionParam(direction)),
                                getAction(characterIdx, ActionType.MasterWeaponAttack, EmptyActionParam())])
        root.buf['attack'] = True
    def Move(root, direction):
        env = root.env
        characterIdx = root.characterIdx
        currentDirection = env.characters[characterIdx]['direction']
        if currentDirection == direction:
            sendAction(root, [getAction(characterIdx, ActionType.Move, EmptyActionParam())])
        else:
            sendAction(root, [getAction(characterIdx, ActionType.TurnAround, TurnAroundActionParam(direction)),
                                getAction(characterIdx, ActionType.Move, EmptyActionParam())])
        root.buf['move'] = True

class Executor:
    def __init__(self):
        pass
    def execute(self, root):
        pass

class Attack:
    class SlaveAttack(Executor):
        def __init__(self):
            super().__init__()
        def execute(self, root):
            PrimitiveOpration.SlaveAttack(root, np.random.randint(0,6))
    class EnemyAttack(Executor): # 攻击敌人
        def __init__(self):
            super().__init__()
        def execute(self, root):
            env = root.env
            myX = root.buf['myX']
            myY = root.buf['myY']
            enemyX = root.buf['enemyX']
            enemyY = root.buf['enemyY']
            myPoint = np.array([myX, myY])
            enemyPoint = np.array([enemyX, enemyY])
            distance = env.distance[0,0]
            if distance > 3 and distance <= 4:
                root.buf['attack'] = True
            elif distance <= 3:
                PrimitiveOpration.AttackToPoint(root, myPoint, enemyPoint)
            else:
                ...
                # 攻击宽松期，此时可以占领地图
    class MapAttack(Executor): # 攻击地图 
        def __init__(self):
            super().__init__()
        def execute(self, root):
            env = root.env
            myX = root.buf['myX']
            myY = root.buf['myY']
            myPoint = np.array([myX, myY])
            maxCountPoint = (0, None)
            for i in range(0,6):
                conquerCount = 0
                searchingPoint = myPoint + np.array(MapAlgarithm.nearPoint[i])
                centerPoint = searchingPoint + np.array(MapAlgarithm.nearPoint[i])
                isPointValid = root.isPointValid(centerPoint)
                if isPointValid and root.isPointDanger(centerPoint):
                    continue
                if isPointValid and env.map[centerPoint[0], -centerPoint[1]] in env.needToAttack:
                    conquerCount += env.needToAttack[env.map[centerPoint[0], -centerPoint[1]]]
                for k in range(0,6):
                    nearPoint = centerPoint + MapAlgarithm.nearPoint[k]  
                    if root.isPointValid(nearPoint) and env.map[nearPoint[0], -nearPoint[1]]  in env.needToAttack:
                        conquerCount += env.needToAttack[env.map[nearPoint[0], -nearPoint[1]]]
                if conquerCount >= 4:
                    PrimitiveOpration.AttackToPoint(root, myPoint, searchingPoint)
                    return
                if conquerCount >= maxCountPoint[0]:
                    maxCountPoint = (conquerCount, searchingPoint)
            PrimitiveOpration.AttackToPoint(root, myPoint, maxCountPoint[1])
            

class Move:
    class FleeMove(Executor): # 逃离移动
        def __init__(self):
            super().__init__()
        def execute(self, root):
            env = root.env
            characterIdx = root.characterIdx
            myX = root.buf['myX']
            myY = root.buf['myY']
            enemyX = root.buf['enemyX']
            enemyY = root.buf['enemyY']
            myPoint = np.array([myX, myY])
            enemyPoint = np.array([enemyX, enemyY])
            distance = env.distance[0,0]
            if distance <= 3:
                fleeTo = MapAlgarithm.FleePath(root, myPoint, enemyPoint, 2)
                if fleeTo is not None:
                    PrimitiveOpration.MoveToPoint(root, myPoint, fleeTo, 'precise')
    class AttackMove(Executor): # 攻击移动
        def __init__(self):
            super().__init__()
        def execute(self, root):
            env = root.env
            characterIdx = root.characterIdx
            myX = root.buf['myX']
            myY = root.buf['myY']
            enemyX = root.buf['enemyX']
            enemyY = root.buf['enemyY']
            myPoint = np.array([myX, myY])
            enemyPoint = np.array([enemyX, enemyY])
            distance = env.distance[0,0]
            if distance > 2: # 如果大于2才继续跟踪，因为如果跟踪得太近，不便于攻击
                path = MapAlgarithm.AStarPathSearch(env, myPoint, enemyPoint)
                if len(path) != 0:
                    PrimitiveOpration.MoveToPoint(root, myPoint, path[-1], 'precise')
    class CdBuffMove(Executor):
        def __init__(self):
            super().__init__()
            self.target = {}
        def execute(self, root):
            env = root.env
            characterIdx = root.characterIdx
            myX = root.buf['myX']
            myY = root.buf['myY']
            enemyX = root.buf['enemyX']
            enemyY = root.buf['enemyY']
            myPoint = np.array([myX, myY])
            enemyPoint = np.array([enemyX, enemyY])
            mindistance = 99
            nearestCDBuff = None
            for cdPoint in env.CDBuff:
                distance = MapAlgarithm.calDistance(cdPoint, myPoint)
                if characterIdx in self.target and cdPoint == self.target[characterIdx]:
                    distance = distance - 2
                if distance < mindistance:
                    mindistance = distance
                    nearestCDBuff = cdPoint
            self.target[characterIdx] = nearestCDBuff
            if nearestCDBuff is not None:
                path = MapAlgarithm.AStarPathSearch(env, myPoint, nearestCDBuff)
                if len(path) != 0:
                    PrimitiveOpration.Move(root, MapAlgarithm.getDirection1(myPoint, path[-1]))
    class HpBuffMove(Executor):
        def __init__(self):
            super().__init__()
            self.target = {}
        def execute(self, root):
            env = root.env
            characterIdx = root.characterIdx
            myX = root.buf['myX']
            myY = root.buf['myY']
            myPoint = np.array([myX, myY])
            minDistance = 99
            nearestHpBuff = None
            for hpPoint in env.hpBuff:
                distance = MapAlgarithm.calDistance(hpPoint, myPoint)
                if characterIdx in self.target and hpPoint == self.target[characterIdx]:
                    distance = distance - 2
                if distance < minDistance:
                    minDistance = distance
                    nearestHpBuff = hpPoint
            self.target[characterIdx] = nearestHpBuff
            if nearestHpBuff is not None:
                path = MapAlgarithm.AStarPathSearch(env, myPoint, nearestHpBuff)
                if len(path) != 0:
                    PrimitiveOpration.Move(root, MapAlgarithm.getDirection1(myPoint, path[-1]))  
                    
    class SmallScaleMapMove(Executor): # 抢占地图追小:
        def __init__(self):
            super().__init__()
            self.target = {}
        def execute(self, root):
            env = root.env
            characterIdx = root.characterIdx
            myX = root.buf['myX']
            myY = root.buf['myY']
            myPoint = np.array([myX, myY])
            minDistance = 99
            nearestOB = None
            for oB in env.otherBlocks:
                distance = MapAlgarithm.calDistance(oB, myPoint)
                if characterIdx in self.target and oB == self.target[characterIdx]:
                    distance = distance - 2
                if distance < minDistance:
                    minDistance = distance
                    nearestOB = oB
            self.target[characterIdx] = nearestOB
            if nearestOB is not None:
                PrimitiveOpration.MoveToPoint(root, myPoint, nearestOB)
    class LargeScaleMapMove(Executor): # 抢占地图移动
        def __init__(self):
            super().__init__()
            self.buf = None
            self.bufTime = 10
        def execute(self, root):
            env = root.env
            characterIdx = root.characterIdx
            X = env.characters[characterIdx]['x']
            Y = env.characters[characterIdx]['y']
            myPoint = np.array([X, Y])
            if self.buf is None or self.bufTime == 0:
                shape = (4,4,4,4)
                unConquerMap = np.zeros((env.mapSize, env.mapSize), dtype=np.float32)
                for key, value in env.needToAttack.items():
                    unConquerMap = unConquerMap + value*(env.map == key).astype(int)
                strides = 8 * np.array([64, 4, 16, 1])
                splitMatrix = np.lib.stride_tricks.as_strided(unConquerMap, shape=shape, strides=strides) 
                splitMaxtix = splitMatrix.sum(axis=-1).sum(axis=-1)
                densePoint = np.unravel_index(np.argmax(splitMaxtix), splitMaxtix.shape)
                densePoint = np.array(densePoint) * 4 + np.array([2,2])
                densePoint[1] = -densePoint[1]
                if not root.isPointValid(densePoint):
                    densePoint = MapAlgarithm.searchValidPoint(root, densePoint, 4)
                self.buf = densePoint
                self.bufTime = 10
            else:
                densePoint = self.buf
                self.bufTime -= 1
            PrimitiveOpration.MoveToPoint(root, myPoint, densePoint, type='precise')


class MapAlgarithm():
    # 4 -10
    # 4 -9
    nearPoint = [[-1,1],[-1,0],[0,-1],[1,-1],[1,0],[0,1]]
    def setDangerInRadius(env, point, radius):
        mapSize = env.mapSize
        env.dangerPoint.append([point[0], -point[1]])
        for rad in range(1, radius+1):
            movingPoint = point + rad * np.array([1,0])
            for near in MapAlgarithm.nearPoint:
                for _ in range(0, rad):
                    if MapAlgarithm.isLegalPoint(movingPoint, mapSize):
                        env.dangerPoint.append([movingPoint[0], movingPoint[1]])
                movingPoint = movingPoint + np.array(near)
    def getNearValidPoint(root, point, raduis, exclude=None):
        movingPoint = point + raduis * np.array([1,0])
        for near in MapAlgarithm.nearPoint:
            for _ in range(0, raduis):
                if exclude is not None and (exclude == movingPoint).all():
                    continue
                if root.isPointValid(movingPoint) and not root.isPointDanger(movingPoint):
                    return movingPoint
                movingPoint = movingPoint + np.array(near)
    def calDistance(point1, point2):
        z1 = 0 - np.sum(point1)
        z2 = 0 - np.sum(point2)
        point_dif = np.array(point1) - np.array(point2)     
        return (abs(point_dif[0]) + abs(point_dif[1]) + abs(z1 - z2))/2
    def getDirection1(point1, point2):
        return MapAlgarithm.nearPoint.index([point2[0]-point1[0], point2[1]-point1[1]])
    def getDirection(point1, point2):
        # if (np.array(point1) == np.array(point2)).all():
        #     return np.random.randint(0,6)
        if point1 is None or point2 is None:
            return -1
        z1 = 0 - np.sum(point1)
        z2 = 0 - np.sum(point2)
        point_dif = point1 - point2     
        distance = (abs(point_dif[0]) + abs(point_dif[1]) + abs(z1 - z2))/2
        if distance == 0:
            return -1
        x = int(point1[0] + (point2[0] - point1[0])  / distance * 1)
        y = int((point1[1] + (point2[1] - point1[1])  / distance * 1))
        return MapAlgarithm.nearPoint.index([x-point1[0], y-point1[1]])
    def isLegalPoint(point, mapSize):
        if point[0] >= 0 and point[0] < mapSize and -point[1] >= 0 and -point[1] < mapSize:
            return True
        else:
            return False
    def searchPoint(env, center, radius, value):
        map = env.map
        mapSize = env.mapSize
        for rad in range(1, radius+1):
            movingPoint = center + rad * np.array([1,0])
            for near in MapAlgarithm.nearPoint:
                for _ in range(0, rad):
                    if MapAlgarithm.isLegalPoint(movingPoint, mapSize) and map[movingPoint[0], -movingPoint[1]] == value:
                        return movingPoint
                    movingPoint = movingPoint + np.array(near)
        return None
    def searchValidPoint(root, center, radius):
        for rad in range(1, radius+1):
            movingPoint = center + rad * np.array([1,0])
            for near in MapAlgarithm.nearPoint:
                for _ in range(0, rad):
                    if root.isPointValid(movingPoint) and not root.isPointDanger(movingPoint):
                        return movingPoint
                    movingPoint = movingPoint + np.array(near)
        return None
    def FleePath(root, myPoint, enemyPoint, radius):
        movingPoint = myPoint + radius * np.array([1,0])
        maxDistancePoint = (0, None)
        for near in MapAlgarithm.nearPoint:
            for _ in range(0, radius):
                if not root.isPointValid(movingPoint) or root.isPointDanger(movingPoint):
                    continue
                distance = MapAlgarithm.calDistance(movingPoint, enemyPoint)
                if distance >= maxDistancePoint[0]:
                    maxDistancePoint = (distance, movingPoint)
                movingPoint = movingPoint + np.array(near)
        return maxDistancePoint[1]
    def AStarPathSearch(env, start, end):
        start = list(start)
        end = list(end)
        map = env.map
        frontier = PriorityQueue()
        frontier.put((0,start))
        cameFrom = dict()
        costSoFar = dict()
        cameFrom[str(start)] = None
        costSoFar[str(start)] = 0
        path = []
        while not frontier.empty():
            current = frontier.get_nowait()[1]
            if (current == end):
                break
            for i in range(0,6):
                next = list(np.array(current) + np.array(MapAlgarithm.nearPoint[i]))
                if not MapAlgarithm.isLegalPoint(next, env.mapSize) or map[next[0], -next[1]] >= 99:
                    continue
                nextCost = costSoFar[str(current)] + env.IDToCost[int(map[next[0], -next[1]])]
                if str(next) not in costSoFar or nextCost < costSoFar[str(next)]:
                    costSoFar[str(next)] = nextCost
                    priority = nextCost + np.abs(next[0] - end[0]) + np.abs(next[1] + end[1])
                    frontier.put_nowait((priority,next))
                    # print(str(next))
                    cameFrom[str(next)] = current
        traceBack = end
        while (cameFrom[str(traceBack)] != None):
                path.append([traceBack[0],traceBack[1]])
                traceBack = cameFrom[str(traceBack)]
        return path
def getAction(characterID, actionType, actionParam):
    return ActionReq(characterID, actionType, actionParam)
def sendAction(root, actions):
    root.env.client.send(PacketReq(PacketType.ActionReq, actions))

class Condition():
    def __init__(self, judgeCode, node=None):
        self.judgeCode = judgeCode
        self.trueChildren = []
        self.falseChildren = []
        if node is not None:
            self.trueChildren.append(node)
    def addChild(self, node, type=True):
        if type:
            self.trueChildren.append(node)
        else:
            self.falseChildren.append(node)
    def execute(self, root):
        env = root.env
        characterIdx = root.characterIdx
        if eval(self.judgeCode):
            for child in self.trueChildren:
                child.execute(root)
        else:
            for child in self.falseChildren:
                child.execute(root)
            
mapLargeMove = Condition(
"root.buf['move'] == False and env.characters[characterIdx]['moveCDLeft'] == 0", Move.LargeScaleMapMove())
mapSmallMove = Condition(
"root.buf['move'] == False and env.characters[characterIdx]['moveCDLeft'] == 0 and env.otherBlockNum <= 20 ", Move.SmallScaleMapMove())
fleeMove = Condition(
"root.buf['move'] == False and env.characters[characterIdx]['moveCDLeft'] == 0", Move.FleeMove())
HpMove = Condition(
"root.buf['move'] == False and env.characters[characterIdx]['moveCDLeft'] == 0 and env.characters[characterIdx]['hp'] < 100", Move.HpBuffMove())
CDMove = Condition(
"root.buf['move'] == False and env.characters[characterIdx]['moveCDLeft'] == 0", Move.CdBuffMove())
enemyAttack = Condition(
"root.buf['attack'] == False and env.characters[characterIdx]['masterWeapon']['attackCDLeft'] == 0", Attack.EnemyAttack())
MapAttack = Condition(
"root.buf['attack'] == False and env.characters[characterIdx]['masterWeapon']['attackCDLeft'] == 0", Attack.MapAttack())
attackMove = Condition(
"root.buf['move'] == False and env.characters[characterIdx]['moveCDLeft'] == 0", Move.AttackMove())
slaveAttack = Condition(
"root.buf['attack'] == False and env.characters[characterIdx]['slaveWeapon']['attackCDLeft'] == 0", Attack.SlaveAttack())

actionTree = ActionTree()
attackConditon = Condition(
"(env.characters[characterIdx]['hp'] > 30 or len(env.hpBuff) == 0) and env.ocharacters[list(env.ocharacters.keys())[0]]['isAlive']") # 攻击CD=0，HP>50，敌方存活 -> 攻击模式 -> 1.发起攻击(为了防止树过深导致反应速度过慢，因此直接传到执行对象) 2.攻击移动
attackConditon1 = Condition("env.ocharacters[list(env.ocharacters.keys())[0]]['isGod']")
attackConditon2 = Condition(
"env.distance[0,0] >= 3"
) # 如果敌方距离过远，就会先移动后攻击
attackConditon1.addChild(fleeMove)
attackConditon1.addChild(mapSmallMove)
attackConditon1.addChild(attackConditon2)
attackConditon2.addChild(attackMove)
attackConditon2.addChild(enemyAttack)
attackConditon2.addChild(enemyAttack, False)
attackConditon2.addChild(attackMove, False)
attackConditon.addChild(attackConditon1)
attackConditon1.addChild(attackConditon2, False)
attackConditon.addChild(MapAttack)

FleeConditon = Condition(
"env.characters[characterIdx]['hp'] <= 30 and env.ocharacters[list(env.ocharacters.keys())[0]]['isAlive']"
) # 如果生命值 <=50且地方存活并且可以移动，则开始逃亡。
FleeConditon.addChild(HpMove)
FleeConditon.addChild(enemyAttack)
SafeBuffSearchMoveCondition = Condition(
"((env.characters[characterIdx]['moveCD'] != 1 and len(env.CDBuff) != 0) or (env.characters[characterIdx]['hp'] < 100 and len(env.hpBuff) != 0)) and not env.ocharacters[list(env.ocharacters.keys())[0]]['isAlive']"
) # HP<50 -> 寻找HPBuff
SafeBuffSearchMoveCondition.addChild(HpMove)
SafeBuffSearchMoveCondition.addChild(CDMove)
SafeBuffSearchMoveCondition.addChild(MapAttack)

MapSearchingCondition = Condition(
"not env.ocharacters[list(env.ocharacters.keys())[0]]['isAlive']"
) # 地图搜索
MapSearchingCondition.addChild(mapSmallMove)
MapSearchingCondition.addChild(mapLargeMove)
MapSearchingCondition.addChild(MapAttack)

attackConditon.addChild(FleeConditon, False)
FleeConditon.addChild(SafeBuffSearchMoveCondition, False)
SafeBuffSearchMoveCondition.addChild(MapSearchingCondition, False)
actionTree.addChild(attackConditon)
actionTree.addChild(slaveAttack)