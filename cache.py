import threading
from cache_block import *

class Cache:
    def print_data(self):
        text = 'Cache '+ self.id + '\n'+'V  Tag  Data \n'
        for block in self.blocks:
            text += (str(block.get_valid())+' '+str(block.get_tag())+' '+str(block.get_data())+'\n')

        print(text)
        
    def __init__(self,id):
        self.id = id
        self.blocks = [Cache_block(x) for x in range(8)]
        return

    def write_data(self,index,tag,new_data):
        self.blocks[index].set_data(new_data)
        self.blocks[index].set_tag(tag)
        self.blocks[index].set_valid(1)
        print("W")
        self.print_data()
        return

    def read_data(self,index,tag):
        if self.blocks[index].get_valid == 1 and self.blocks[index].get_tag == tag:
            return self.blocks[index].get_data
        else:
            return 'CACHE MISS'

    def invalid_cache_block(self,index,tag):
        if self.blocks[index].get_tag == tag:
            self.blocks[index].set_valid(0)
        print("V")
        self.print_data()
        

    def verify_update(self,index,tag,data):
        if self.blocks[index].get_tag == tag:
            self.blocks[index].set_data(data)
        print("U")
        self.print_data()
        
