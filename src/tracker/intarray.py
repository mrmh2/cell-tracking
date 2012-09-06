class InteractorArray:
    def __init__(self, array, shifts):
        self.array = array
        self.shifts = shifts
        #self.rs = 0
        #self.gs = 8
        #self.bs = 16

    def mouse_click(self, (x, y), button):
        #print "Clicked at (%d, %d), button %d" % (x, y, button)
        #print "Val is", self.array[x, y]
        #print "Cid is", aval_to_cid(self.array[x, y])
        cid = self.aval_to_cid(self.array[x, y])

        self.onclick(cid)

    def aval_to_cid(self, val):
        #rs = self.rs
        #gs = self.gs
        #bs = self.bs
        rs, bs, gs, _ = self.shifts
        #g, b, r = (val >> 8) % 256, (val >> 16) % 256, (val >> 0) % 256
        r, g, b = (val >> rs) % 256, (val >> gs) % 256, (val >> bs) % 256
        #r, b, = b, r
        return (r << 16) + (g << 8) + (b << 0)


