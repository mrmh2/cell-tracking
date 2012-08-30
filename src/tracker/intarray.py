def aval_to_cid(val):
    g, b, r = (val >> 8) % 256, (val >> 16) % 256, (val >> 0) % 256
    return (r << 16) + (g << 8) + (b << 0)

class InteractorArray:
    def __init__(self, array):
        self.array = array

    def mouse_click(self, (x, y), button):
        print "Clicked at (%d, %d), button %d" % (x, y, button)
        print "Val is", self.array[x, y]
        print "Cid is", aval_to_cid(self.array[x, y])
        cid = aval_to_cid(self.array[x, y])

        self.onclick(cid)
