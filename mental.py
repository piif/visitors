pmin = 9*8*7*6*5*4*3*2
tmin = []

def tester(l):
    global pmin, tmin
    p1 = l[0]*l[1]*l[2]
    if (p1 >= pmin):
        return
    p2 = l[3]*l[4]*l[5] 
    if (p2 >= pmin):
        return
    p3 = l[6]*l[7]*l[8]
    if (p3 >= pmin):
        return
    p4 = l[0]*l[3]*l[6]
    if (p4 >= pmin):
        return
    p5 = l[1]*l[4]*l[7]
    if (p5 >= pmin):
        return
    p6 = l[2]*l[5]*l[8]
    if (p6 >= pmin):
        return

    p = [ p1, p2, p3, p4, p5, p6 ]
    p.sort()
    pmin = p[5]
    tmin = l

    print "{:^5}{:^5}{:^5} - {:^5}".format(l[0],l[1],l[2],p1)
    print "{:^5}{:^5}{:^5} - {:^5}".format(l[3],l[4],l[5],p2)
    print "{:^5}{:^5}{:^5} - {:^5}".format(l[6],l[7],l[8],p3)
    print "{:^5}{:^5}{:^5} =>{:^5}".format(p4, p5, p6, pmin)

def combi(head, tail, func):
    if len(tail) == 1:
        func(head + tail)
        return
    for i in range(len(tail)):
        combi(head + [ tail[i] ], tail[:i] + tail[i+1:], func)


print pmin, " tests a faire ..."
t = range(1,10)
combi([], t, tester)
