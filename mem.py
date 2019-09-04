#!/usr/bin/python
import threading
import time
import matplotlib.pyplot as plt
import numpy as np

class MEM:
    def draw(self):
        self.fig = plt.figure(dpi=80)
        self.ax = self.fig.add_subplot(1,1,1)
        self.fig.show()
        self.columns = ('Address', 'Data')
        while True:
            table_data=[]
            for i in range(16):                
                table_data.append([i,self.registers[i]])
            table = self.ax.table(cellText=table_data,                             
                             colLabels=self.columns,
                             loc='center')
            table.set_fontsize(14)
            table.scale(1,1.7)
            self.ax.axis('off')
            self.fig.canvas.draw()
            time.sleep(0.1)
            print("drawing mem")
        
    def __init__(self,id):
        self.id = id
        self.registers = [0 for x in range(16)]        
        #threading.Thread(target=self.draw).start()
        return

    def update_data(self,address,new_data):
        self.registers[address] = new_data
        #print("MEM")
        #print(self.registers)
        return

    def read_data(self,address):
        return self.registers[address]
    
    

        
        
        
