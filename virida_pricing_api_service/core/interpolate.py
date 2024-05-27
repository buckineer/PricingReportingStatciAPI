class Interpolate:
    def __init__(self, x: list, y: list):
        if len(x) != len(y):
            raise ValueError("The number of values in x-axis must be the same as in y-axis")

        if any(x2 - x1 <= 0 for x1, x2 in zip(x, x[1:])):
            raise ValueError("Values in x-axis must be in strictly ascending order")
      
        self.x = x
        self.y = y
        self.intervals = list(zip(x, x[1:], y, y[1:]))
        self.slopes = [(y2 - y1) / (x2 - x1) for x1, x2, y1, y2 in self.intervals]


    def __call__(self, x):
        if x < 0:
            raise ValueError("X must be a positive value")
        
        if x <= self.x[0]:
            return self.y[0]
        elif x > self.x[0] and x < self.x[-1]:
            x1, x2, y1, y2 = next((x1, x2, y1, y2) for x1, x2, y1, y2 in self.intervals if x >= x1 and x <= x2)
            return y1 + ((x - x1) / (x2 - x1)) * (y2 - y1)
        else:
            return self.slopes[-1] * (x - self.x[-1]) + self.y[-1]

