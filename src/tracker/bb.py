class BoundingBox():
    def __init__(self, (x, y), (xdim, ydim)):
        self.x = x
        self.y = y
        self.xdim = xdim
        self.ydim = ydim

    def scale(self, scale_factor):
        xdim = int(scale_factor * self.xdim)
        ydim = int(scale_factor * self.ydim)

        return BoundingBox((self.x, self.y), (xdim, ydim))
