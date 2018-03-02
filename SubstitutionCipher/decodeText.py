#!/usr/bin/python

import sys
import languageModelLib
import decodeTextLib

encoded_message = sys.argv[1]
model = languageModelLib.readInModel("model.txt")
d = decodeTextLib.decodeMessage(encoded_message, model, 10000)
print "*****"
print d