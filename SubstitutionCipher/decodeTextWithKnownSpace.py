#!/usr/bin/python

import sys
import languageModelLib
import decodeTextLib

known_space = sys.argv[1]
if (len(known_space) != 1):
  print "First argument should be the known encoded space. You put: " + known_space
  print "The argument must be a single character"
  exit()

print "Using Space: " + known_space

encoded_message = sys.argv[2]
model = languageModelLib.readInModel("model.txt")
d = decodeTextLib.decodeMessage(encoded_message.upper(), model, 10000, known_space)
print "*****"
print d