import threading
import time
from cache import *

class Control_cache:
    def read_bus(self):
        while True:
            cpu,tipe,address = self.bus.read_type_address_inst()
            if cpu != self.id and tipe == 'W':
                index = address % 8
                tag = address // 8
                self.cache.invalid_cache_block(index,tag)
    
    def __init__(self,id,bus,cache,other_caches):
        self.id = id
        self.bus = bus
        self.cache = cache
        self.other_caches = other_caches 
        self.thread = threading.Thread(target=self.read_bus).start()
        return
    
    def update_data(self,address):
        value = self.bus.acquire_bus(self.id,address,'R')
        index = address % 8
        tag = address // 8
        self.cache.write_data(index,tag,value)
        for cache in self.other_caches:
            #Esto se hace si es necesario que el controlador actualice las demas caches cuando lee
            cache.verify_update(index,tag,value)

    def write_data_mem(self,address,data):
        self.bus.acquire_bus(self.id,address,'W')
        index = address % 8
        tag = address // 8
        for cache in self.other_caches:
            #Esto se hace si es necesario que el controlador actualice las demas caches cuando lee
            cache.invalid_cache_block(index,tag)
