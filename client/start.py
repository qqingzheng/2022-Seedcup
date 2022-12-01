from env import *
import sys
from agent import actionTree
from libs.config import Config
from time import sleep
import socket
def set_seed(seed=20021004):
    np.random.seed(seed)
def train(test=False):
    env = Env(2,2, startUI=True)
    while True:
        update = env.refresh()
        if update:
            actionTree.execute(env, 0)
        else:
            break
if __name__ == "__main__":
    set_seed()
    train(False)