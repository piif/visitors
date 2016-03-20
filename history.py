from random import randint
followers = []

frameNumber = 0
refreshPathRate = 4

def refreshPath():
    global followers, frameNumber, refreshPathRate
    ttl = frameNumber - refreshPathRate / 2
    print "refreshPath", ttl, "on", len(followers), "elements"
    followers = [ x for x in followers if not f['f'] < ttl ]
    print "=>", len(followers)

for frameNumber in range(20):
    r = randint(1, 100);
    item = { 'f':frameNumber, 'i':r }
    followers.append(item)
    print "before", followers
    refreshPath()
    print "after ", followers
