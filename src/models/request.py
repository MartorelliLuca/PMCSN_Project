class Request:

    def __init__(self, ID):
            self.ID = ID
            self.creation_time = None
            self.destr_time = None

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
    
    