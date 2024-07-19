import os
def getlogin():
    ''' On WSL, os.getlogin() fails so we need the less reliable environment variable 'USER' '''
    try:
        return os.getlogin()
    except:
        return os.getenv('USER')