#!/usr/bin/python

import languageModelLib
import decodeTextLib
import sys

message = sys.argv[1].upper()

charsInMessageList = list(set(message))
charsInMessageList.sort()
charsInMessage = ''.join(charsInMessageList)

key = decodeTextLib.randomTranspose(len(charsInMessage))

model = languageModelLib.readInModel("model.txt")

print "Original Message: ", message
print "Original Message Entropy: ", languageModelLib.entropyOfText(message, model, True)

print "\nTransposition Key"
print "THESE CHARACTERS: --" + ''.join(charsInMessage) + "--"
print "          MAP TO: --" + ''.join(key) + "--"

encoded_message = decodeTextLib.transformText(message, charsInMessage, key)
print "\nEncoded Message: ", encoded_message
print "Encoded Message Entropy: ", languageModelLib.entropyOfText(encoded_message, model, True)