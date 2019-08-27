from clock import *

def main():
    try:
        clock = Clock(1,6)
        clock.initialize_clock()
    except Exception as e:
        print(e)

main()
