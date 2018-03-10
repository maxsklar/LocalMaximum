#!/usr/bin/python

import sys
import languageModelLib
import decodeTextLib

encoded_message = sys.argv[1].upper()
model = languageModelLib.readInModel("model.txt")

init_entropy = languageModelLib.entropyOfText(encoded_message, model)
print "INITIAL ENTROPY: " + str(init_entropy)

d = decodeTextLib.decodeMessage(encoded_message, model, 10000)
print "*****"
print d