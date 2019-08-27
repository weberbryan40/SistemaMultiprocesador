import random

class Instruction_fetch:
    def __init__(self,id):
        self.id = id
        return

    def create_new_instruction(self):
        tipe = random.choice(['M','P'])
        if tipe == 'M':
            tipe = random.choice(['W','R'])
            address = random.choice(range(16))
            cycles = 2
        else:
            cycles = 1
            address = -1
        return [tipe,cycles,address]




