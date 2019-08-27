class Cache_block:
    def __init__(self,index):
        self.valid = 0
        self.index = index
        self.tag = 0
        self.data = 0
        return

    def set_tag(self,new_tag):
        self.tag = new_tag
        return

    def get_tag(self):
        return self.tag

    def set_valid(self,value):
        self.valid=value
        return

    def get_valid(self):
        return self.valid

    def set_data(self,new_data):
        self.data = new_data
        return

    def get_data(self):
        return self.data
