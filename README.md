pre-Processing tools
=====

VideoReader
-----
Simple class to read a capture, play/pause/backward some frames
This class can be used as main template for other programs 

sampleCapture
-----
**TODO**
Read a file, detect background, split in video extracts containing movements

stabilize
-----
Given a "reference" polygon, stabilize image by forcing polygon coordinates

detection tools
=====

diffImg
-----
Some test in diffing two images to extract movement and polygons in them

shapes
-----
shape detection in a single image

diffThreshold
-----
Same tests, with first frame as reference
polygon detection, "follower" algorithm to detect trajectory of polygons
TODO : retry with another bg subtractor and better "main loop"

BackgroundSubtractorMOG
-----
First tests with BackgroundSubtractorMOG method to extract background

lineFilter
-----
Another try : detect crossing thru 2 reference lines
May works fine if people don't collide, but still need work on way to deduce movement direction from various cases

*Gate* : class to handle "2 lines" concept in lineFilter


other
=====

History
-----
**TODO**
class to keep track of several steps in a program

pedestrians
-----
Body detection, from http://www.pyimagesearch.com/2015/11/09/pedestrian-detection-opencv
Works fine only in front view

flow
-----
???

historyTest
-----
test code on storing data with ttl

  