import threading

class Cache:
    self.registers = [0 for x in range(8)]
    
    def __init__(self,id):
        self.id = id
        return

    def update_data(self,address,new_data):
        self.registers[address] = new_data
        return
