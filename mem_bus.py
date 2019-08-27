import threading
import time
from mem import *

class Memory_bus:
    def __init__(self,id):
        self.id = id
        self.mutex = threading.Lock()
        self.memory = MEM(1)
        self.cpu_in_bus = ''
        self.tipe = ''
        self.address = -1
        return

    def acquire_bus(self,cpu,address,tipe):
        #self.mutex.acquire()
        self.cpu_in_bus = cpu
        self.tipe = tipe
        self.address
        if tipe == 'W':
            return self.memory.update_data(address,cpu)
        else:
            return self.memory.read_data(address)

    def release_bus(self):
        #self.mutex.release()
        print("")

    def get_cpu_in_bus(self):
        return self.cpu_in_bus

    def read_type_address_inst(self):
        return [self.cpu_in_bus,self.tipe,self.address]
