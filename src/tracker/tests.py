#!/usr/bin/env python2.7

import bb

def test_contains(myb, (x, y)):
    print "Testing if bb contains %d,%d:" % (x, y), myb.contains((x, y))

def test_bb():
    myb = bb.BoundingBox((10, 10), (100, 100))
    
    for x in range(0, 121, 60):
        for y in range(0, 121, 60):
            test_contains(myb, (x, y))


    # TODO - edge cases (literally!)

def main():
    test_bb()

if __name__ == '__main__':
    main()
