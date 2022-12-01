import json, os
import time
import numpy as np
from start import train, set_seed
if __name__ == "__main__":
    with open("./config.json", mode="r") as file:
        config_file = json.load(file)
    totalScore = 0
    testTimes = 5
    
    for i in range(testTimes):
        # os.system("pgrep seedcupServer | xargs kill")
        # os.system("pgrep bot | xargs kill")
        port = np.random.randint(25565, 28000) + int(time.time()) % 1000
        seed = np.random.randint(0, 20021009)
        with open("./config.json", mode="w") as file:
            config_file['Port'] = port
            config_file['RandomSeed'] = seed
            config_file['GameMaxFrame'] = 600
            json.dump(config_file, file)
        os.system("nohup ./seedcupServer > server.out 2>&1 &")
        os.system("nohup ./bot > bot.out 2>&1 &")
        os.system("nohup python client/start.py > client.out 2>&1")
        with open("result.out", "r") as file:
            score = int(file.readline())
            print(f"Seed: {seed} Test{i}: {score}")
            totalScore += score
        os.remove("result.out")
    os.remove("bot.out")
    os.remove("client.out")
    os.remove("server.out")
    print(f"AvgScore: {totalScore/testTimes}")