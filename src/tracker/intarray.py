class InteractorArray:
    def __init__(self, array, shifts):
        self.array = array
        self.shifts = shifts

    def mouse_click(self, (x, y), button):
        #print "Clicked at (%d, %d), button %d" % (x, y, button)
        #print "Val is", self.array[x, y]
        #print "Cid is", aval_to_cid(self.array[x, y])
        cid = self.aval_to_cid(self.array[x, y])

        print 'Clicked cid was', cid

        self.onclick(cid)

    def aval_to_cid(self, val):
        rs, gs, bs, _ = self.shifts
        r, g, b = (val >> rs) % 256, (val >> gs) % 256, (val >> bs) % 256
        return (r << 16) + (g << 8) + (b << 0)


