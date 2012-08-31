#!/usr/bin/env python2.7

import os
import sys

import celldata

class MatchData():
    
    def __init__(self, celldata_from, celldata_to):
        self.cdfrom = celldata_from
        self.cdto = celldata_to

        #ls1 = [cell.lnumbers for cell in self.cdfrom]
        for cell in self.cdfrom:
            print type(cell)

def main():
    #try:
    #    image_file1 = sys.argv[1]
    #    image_file2 = sys.argv[2]
    #except:
    #    print "Usage %s image_file1 image_file2" % os.path.basename(sys.argv[0])
    #    sys.exit(0)

    ifile1 = 'data/newexp/segmented_image/T05.png'
    ifile2 = 'data/newexp/segmented_image/T06.png'
    lfile1 = 'data/newexp/l_numbers/T05.txt'
    lfile2 = 'data/newexp/l_numbers/T06.txt'

    celldata1 = celldata.CellData(ifile1, lfile1)
    celldata2 = celldata.CellData(ifile2, lfile2)

    md = MatchData(celldata1, celldata2)

if __name__ == '__main__':
    main()
