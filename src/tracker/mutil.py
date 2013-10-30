import os
import re
import errno

def mean(it):
    return sum(it) / len(it)

def msum(l):
    if len(l) == 1:
        return l[0]
    else:
        return sum(l[1:], l[0])

def sorted_nicely( l ):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)

def mkdir_p(path):
    try:
        os.makedirs(path)   
    except OSError as exc:
        # FIXME
        if exc.errno == errno.EEXIST:
            pass
        else: raise

def top_fraction(l, frac):
    pass


