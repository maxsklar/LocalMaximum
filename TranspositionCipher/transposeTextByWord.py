#!/usr/bin/python

import random
import math
import re
import languageModelLib
import decodeText

#message = "hello my name is max nice to meet you i am from new york what is your name".upper()
#message = "Cuban comedian denounces discriminatory policies and attitudes on island".upper()
#message = "A fantastic opportunity to join a fast growing team in New York City tech that is truly making a difference in mesh networking".upper()
message = "New York is the best".upper()
#message = "These Vintage Photos From Circus Sideshows Are the Stuff Nightmares Are Made Of".upper()
#message = "Funny how the Fake News Media doesnt want to say that the Russian group was formed in Twenty Fourteen long before my run for President  Maybe they knew I was going to run even though I didnt know".upper()
#message = "The Senate of the United States shall be composed of two Senators from each State elected by the people thereof for six years and each Senator shall have one vote  The electors in each State shall have the qualifications requisite for electors of the most numerous branch of the State legislatures".upper()
#message = "Nearly ten years had passed since the Dursleys had woken up to find their nephew on the front step but Privet Drive had hardly changed at all The sun rose on the same tidy front gardens and lit up the brass number four on the Dursleys front door it crept into their living room which was almost exactly the same as it had been on the night when Mr Dursley had seen that fateful news report about the owls".upper()
message = "Double double toil and trouble  Fire burn and caldron bubble  Cool it with a baboons blood  Then the charm is firm and good".upper()

charsInMessageList = list(set(message))
charsInMessageList.sort()
charsInMessage = ''.join(charsInMessageList)

key = decodeText.randomTranspose(len(charsInMessage))
print "Original Key: ", ''.join(key)

encoded_message = decodeText.transformText(message, charsInMessage, key)
print "Original Encoded Message: ", encoded_message

model = languageModelLib.readInModel("model.txt")

print "Original Message: ", message
print "Original Message Entropy: ", languageModelLib.entropyOfTextGivenStrategy(message, model, True)

strategy = decodeText.SEARCH_STRATEGY_MARKOV_CHAIN
d = decodeText.decodeMessage(encoded_message, model, strategy, True, 10000)
print "*****"
print d