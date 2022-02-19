'''
Executes a command, to be used in conjunction with run.py to invoke non
python3 scripts.

Created on 18 Feb 2022

@author: gianni
'''

from subprocess import Popen
import sys

def main():
    command = sys.argv[1:]
    print("running: ", command)
    try:
        return Popen(command).wait()
    finally:
        print("completed: ", command)
        
if __name__ == '__main__':
    exit(main())