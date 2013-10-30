#!/usr/bin/env python2.7

import celldata
import threading
import multiprocessing

class CellLoader(threading.Thread):
    def __init__(self, ifile):
        self.ifile = ifile
        threading.Thread.__init__(self)

    def run(self):
        self.celld = celldata.CellData(self.ifile)

    @property
    def cd(self):
        return self.celld

class PCellLoader(multiprocessing.Process):
    def __init__(self, ifile):
        self.ifile = ifile
        multiprocessing.Process.__init__(self)
        self.celld = None

    def run(self):
        self.celld = celldata.CellData(self.ifile)

    @property
    def cd(self):
        return self.celld

def threaded_main():
    ifile1 = 'data/newexp/segmented_image/T05.png'
    #cd1 = celldata.CellData(ifile1)


    ifile2 = 'data/newexp/segmented_image/T06.png'
    #cd2 = celldata.CellData(ifile2)

    ml1 = CellLoader(ifile1)
    ml2 = CellLoader(ifile2)
    ml3 = CellLoader(ifile2)
    ml4 = CellLoader(ifile2)
    ml5 = CellLoader(ifile2)
    ml1.start()
    ml2.start()
    ml3.start()
    ml4.start()
    ml5.start()

    print threading.activeCount()

    #ml1.join()
    #ml2.join()
    #cd1 = ml1.cd
    #cd2 = ml2.cd

    #print cd1[20].centroid
    #print cd2[21].centroid

def main():
    ifile1 = 'data/newexp/segmented_image/T05.png'
    ifile2 = 'data/newexp/segmented_image/T06.png'

    ml1 = PCellLoader(ifile1)
    ml2 = PCellLoader(ifile2)
    ml3 = PCellLoader(ifile2)
    ml4 = PCellLoader(ifile2)
    ml5 = PCellLoader(ifile2)
    
    ml1.start()
    ml2.start()
    ml3.start()
    ml4.start()
    ml5.start()

    ml1.join()
    ml2.join()
    ml3.join()
    ml4.join()
    ml5.join()

    cd1 = ml5.cd

    print cd1[20].centroid
    

if __name__ == '__main__':
    main()
