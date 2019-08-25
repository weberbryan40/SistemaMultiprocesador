from clock import *
from cpu import *

def main():
    try:

        cpus=[CPU(1),CPU(2),CPU(3),CPU(4)]
        
        clock = Clock(1,cpus)
        clock.initialize_clock()

    except Exception as e:
        print(e)

main()
