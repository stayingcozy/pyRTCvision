class RollingAverage():

    def __init__(self, windowSize):

        self.windowSize = windowSize
        self.values = []
        self.sum = 0

    def addValue(self,value):
        self.values.append(value)
        self.sum += value

        # Remove oldest value if window size is exceeded
        if len(self.values) > self.windowSize:
            removedValue = self.values.pop(0)
            self.sum -= removedValue

    def getAverage(self):
        return self.sum / len(self.values)


