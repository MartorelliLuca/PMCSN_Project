class Person:
    def __init__(self, ID, entry, creation_time):
        self.entry = entry
        self.creation_time = creation_time
        self.ID = ID
        self.destr_time = None


    def getCreationTime(self):
        return self.creation_time

    def getID(self):
        return self.ID

    def getEntry(self):
        return self.entry

    def getDestrTime(self):
        return self.destr_time

    def setDestrTime(self, destr_time):
        self.destr_time = destr_time

    