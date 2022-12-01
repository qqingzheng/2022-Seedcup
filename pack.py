import os, sys

if __name__ == "__main__":
    if os.path.exists("./submit_py.zip"):
        os.system("rm ./submit_py.zip")
    os.system("mkdir ./submit_py")
    os.system("cp -r ./client ./submit_py")
    os.system("cp ./config.json ./start.sh ./requirements.txt ./prepare.sh  ./submit_py")
    os.system("zip -r submit_py.zip ./submit_py")
    os.system("rm -r ./submit_py")