class Request:

    def __init__(self, ID,creation_time):
            self.ID = ID
            self.creation_time = creation_time
            self.destr_time = None
            self.time_to_fill_out = 30
            self.times_tried_to_fill_out = 1

    def setCreationTime(self, creation_time):
        self.creation_time = creation_time

    def setDestrTime(self, destr_time):
        self.destr_time = destr_time

    def getCreationTime(self):
        return self.creation_time

    def getDestrTime(self):
        return self.destr_time

    def getID(self):
        return self.ID
    
    