#!/usr/bin/python

import random
import math
import re

Characters = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ ')
EndSentencePunct = list('.?!')

def randomTranspose(chars):
  copy = list(chars)
  random.shuffle(copy)
  return copy

def randomSingleCharTranspose(chars):
  L = len(chars)
  copy = list(chars)
  first_ix = random.randint(0, L - 1)
  second_ix = random.randint(0, L - 1)
  c = copy[first_ix]
  copy[first_ix] = copy[second_ix]
  copy[second_ix] = c
  return copy

def transformChar(char, transpose):
  indexOf = transpose.index(char)
  if (indexOf == -1): raise ValueError('bad chararacter' . char)
  return Characters[indexOf]

def transformText(text, transpose):
  chars = list(text.upper())
  trans_chars = map(lambda x: transformChar(x, transpose), chars)
  return ''.join(trans_chars)

def readAndSimplifyFile(filename, char_list):
  f = open(filename, "r")
  for raw_line in f:
    sentences = re.split('\\.|\\?|\\!', raw_line)
    for sentence in sentences:
      filtered_sentence = [x for x in list(sentence.upper()) if x in char_list]
      if (len(filtered_sentence) == 0): continue
      yield ''.join(filtered_sentence)

def characterBagModel(filtered_sentences):
  total = 0
  hist = {}
  for sentence in filtered_sentences:
    for char in list(sentence):
      currenctCount = hist.get(char, 0)
      hist[char] = currenctCount + 1
      total += 1
  char_log_probs = {}
  for char in Characters:
    char_prob = (hist.get(char, 0) + (1.0 / len(Characters))) / (total + 1.0)
    char_log_probs[char] = -1 * math.log(char_prob)
  return char_log_probs

def entropyOfText(text, char_log_probs):
  entropy = 0.0
  for char in list(text):
    entropy += char_log_probs[char]
  return entropy

def new_text_accept(old_text, new_text, char_log_probs):
  entropy_diff = entropyOfText(new_text, char_log_probs) - entropyOfText(old_text, char_log_probs)
  prob = math.exp(entropy_diff)
  accept = prob > random.random()
  return accept

def decodeMessage(message, iters):
  print "Original Encoded Message: ", message
  x = readAndSimplifyFile("textSamples/newyork.txt", Characters)
  char_log_probs = characterBagModel(x)
  old_transformed = message
  old_transpose = Characters
  old_entropy = entropyOfText(message, char_log_probs)

  for i in range(0, iters):
    if (i % 1000 == 0):
      print i, old_transformed, ''.join(old_transpose), old_entropy

    new_transpose = randomSingleCharTranspose(old_transpose)
    new_transformed = transformText(message, new_transpose)
    new_entropy = entropyOfText(new_transformed, char_log_probs)

    entropy_diff = new_entropy - old_entropy
    accept = math.exp(entropy_diff) < random.random()

    if (accept):
      old_transformed = new_transformed
      old_transpose = new_transpose
      old_entropy = new_entropy

  return old_transformed

key = randomTranspose(Characters)
print "Original Key: ", key
message = "hello my name is max nice to meet you i am from new york what is your name".upper()
encoded_message = transformText(message, key)
d = decodeMessage(message, 20000)
print "*****"
print d
