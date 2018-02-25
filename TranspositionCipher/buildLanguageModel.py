#!/usr/bin/python

import languageModelLib
from os import path, walk

Characters = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ ')

def getSampleTextfiles():
  for root, subFolders, files in walk("./textSamples"):
    for filename in files:
      if (filename.endswith(".txt")):
        yield path.join(root, filename)

def readAndSimplifyFiles(filenames):
  for filename in filenames:
    print "Reading File " + filename
    f = open(filename, "r")
    for raw_line in f:
      sentences = re.split('\\.|\\?|\\!', raw_line)
      for sentence in sentences:
        filtered_sentence = [x for x in list(sentence.upper()) if x in Characters]
        if (len(filtered_sentence) == 0): continue
        yield ''.join(filtered_sentence)

files = getSampleTextfiles()
training_data = readAndSimplifyFiles(files)
model = languageModelLib.buildModel(training_data, 5)
languageModelLib.outputModel(model, "model.txt")