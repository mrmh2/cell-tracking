def mean(it):
    return sum(it) / len(it)

def msum(l):
    if len(l) == 1:
        return l[0]
    else:
        return sum(l[1:], l[0])
