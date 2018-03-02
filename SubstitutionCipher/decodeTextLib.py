#!/usr/bin/python

import random
import math
import re
import languageModelLib

Characters = list(' ABCDEFGHIJKLMNOPQRSTUVWXYZ')
NumCharacters = len(Characters)
EndSentencePunct = list('.?!')

def randomTranspose(numberToSelect):
  copy = list(Characters)
  random.shuffle(copy)
  return copy[:numberToSelect]

# In this case, we already know which character is the space
def randomTransposeGivenSpace(numberToSelect, space):
  copy = list(Characters)
  random.shuffle(copy)
  copy = transposeIndecies(copy, 0, copy.index(space))
  return copy[:numberToSelect]


def randomSingleCharTranspose(transpose):
  L = len(transpose)
  first_ix = random.randint(0, L - 1)
  
  second_ix = random.randint(0, NumCharacters - 1)
  second_char = Characters[second_ix]
  
  if (second_char in transpose):
    index_to_swap = transpose.index(second_char)
    return transposeIndecies(transpose, first_ix, index_to_swap)
  
  copy = list(transpose)
  copy[first_ix] = second_char
  
  return copy

def randomSingleCharTransposeNotSpace(transpose):
  L = len(transpose)
  first_ix = random.randint(1, L - 1)

  second_ix = random.randint(0, NumCharacters - 2)
  second_char = Characters[second_ix]

  if (second_char in transpose):
    index_to_swap = transpose.index(second_char)
    return transposeIndecies(transpose, first_ix, index_to_swap)

  copy = list(transpose)
  copy[first_ix] = second_char

  return copy
    
def generateAllSingleCharTransposes(transpose):
  allTransposes = []
  L = len(transpose)
  for first_ix in range(0, L):
    for second_ix in range(0, NumCharacters):
      second_char = Characters[second_ix]
      
      if (second_char in transpose):
        index_to_swap = transpose.index(second_char)
        if (index_to_swap <= first_ix): continue
        allTransposes.append(''.join(transposeIndecies(transpose, first_ix, index_to_swap)))
      else:
        copy = list(transpose)
        copy[first_ix] = second_char
        allTransposes.append(''.join(copy))
  return allTransposes

def generateAll2CharTransposes(transpose):
  allTransposes = []
  L = len(transpose)
  for first_ix in range(0, L):
    for second_ix in range(first_ix + 1, L):
      for third_ix in range(0, NumCharacters):
        third_char = Characters[second_ix]

        if (third_char in transpose):
          third_char_index_to_swap = transpose.index(third_char)
          if (third_char_index_to_swap <= second_ix): continue
          
          transpose2 = transposeIndecies(transpose, first_ix, second_ix)
          transpose3 = transposeIndecies(transpose, first_ix, third_char_index_to_swap)
          allTransposes.append(transpose3)
          
          transpose2 = transposeIndecies(transpose, first_ix, third_char_index_to_swap)
          transpose3 = transposeIndecies(transpose, first_ix, second_ix)
          allTransposes.append(transpose3)
        else:
          copy = list(transpose)
          copy[first_ix] = transpose[second_ix]
          copy[second_ix] = third_char
          allTransposes.append(''.join(copy))
          
          copy = list(transpose)
          copy[first_ix] = third_char
          copy[second_ix] = transpose[first_ix]
          allTransposes.append(''.join(copy))
          
  return allTransposes
    
def transposeIndecies(chars, first_ix, second_ix):
  copy = list(chars)
  c = copy[first_ix]
  copy[first_ix] = copy[second_ix]
  copy[second_ix] = c
  return ''.join(copy)

def transformChar(char, charsInMessage, transpose):
  indexOf = charsInMessage.index(char)
  return transpose[indexOf]

def transformText(text, charsInMessage, transpose):
  chars = list(text)
  trans_chars = map(lambda x: transformChar(x, charsInMessage, transpose), chars)
  return ''.join(trans_chars)

def chooseSpacePlacement(text, model, smoothingConstant = 50.0):
  lowestEnt = float("inf")
  hist = {}
  for candidate in Characters:
    newText = text.replace(" ", "-").replace(candidate, " ").replace("-", candidate)
    ent = languageModelLib.entropyOfSpacePlacement(newText, model, smoothingConstant = 50.0)
    hist[candidate] = ent
    if (ent < lowestEnt): lowestEnt = ent

  S = 0
  for key in hist:
    unnormed_prob = math.exp(lowestEnt - hist[key])
    hist[key] = unnormed_prob
    S += unnormed_prob

  for key in hist: hist[key] /= S
  return weighted_random_by_dct(hist)

def weighted_random_by_dct(dct):
  rand_val = random.random()
  total = 0
  for k, v in dct.items():
    total += v
    if rand_val <= total: return k
  assert False, 'unreachable'

def decodeMessageTrialMarkov(message, model, steps):
  charsInMessageList = list(set(message))
  charsInMessageList.sort()
  charsInMessage = ''.join(charsInMessageList)

  space = chooseSpacePlacement(message, model)

  old_transpose = randomTransposeGivenSpace(len(charsInMessage), space)
  old_transformed = transformText(message, charsInMessage, old_transpose)
  old_entropy = languageModelLib.entropyOfText(old_transformed, model)

  i = 0
  while i < steps:
    new_transpose = randomSingleCharTransposeNotSpace(old_transpose)
    new_transformed = transformText(message, charsInMessage, new_transpose)
    new_entropy = languageModelLib.entropyOfText(new_transformed, model)

    entropyDiff = old_entropy - new_entropy
    accept = True if entropyDiff > 0 else math.exp(old_entropy - new_entropy) > random.random()

    if (accept):
      old_transformed = new_transformed
      old_transpose = new_transpose
      old_entropy = new_entropy

    i += 1

  # Finish Off With Hill Climbing

  remainingTransposes = generateAllSingleCharTransposes(old_transpose)
  random.shuffle(remainingTransposes)
  transposeStrategy = "Single"
  
  while len(remainingTransposes) > 0:
    new_transpose = remainingTransposes[0]

    new_transformed = transformText(message, charsInMessage, new_transpose)
    new_entropy = languageModelLib.entropyOfText(new_transformed, model)

    accept = new_entropy < old_entropy

    if (accept):
      old_transformed = new_transformed
      old_transpose = new_transpose
      old_entropy = new_entropy

      remainingTransposes = generateAllSingleCharTransposes(old_transpose)
      random.shuffle(remainingTransposes)
      transposeStrategy = "Single"
    else:
      remainingTransposes = remainingTransposes[1:]
      
      if (len(remainingTransposes) == 0) and (transposeStrategy == "Single"):
        transposeStrategy = "Double"
        remainingTransposes = generateAll2CharTransposes(old_transpose)

  return old_transpose, old_transformed, old_entropy, i

def decodeMessage(message, model, trials):
  best_encoding_entropy = float("inf")
  best_transpose = None
  best_transformed = None
  
  for trial in range(0, trials):
    result = decodeMessageTrialMarkov(message, model, 1000)
    
    old_transpose, old_transformed, old_entropy, num_steps = result
    
    if (old_entropy < best_encoding_entropy):
      # Trial is accepted
      best_encoding_entropy = old_entropy
      best_transpose = old_transpose
      best_transformed = old_transformed
    
    print "TRIAL " + str(trial), "STEPS: " + str(num_steps), old_transformed, " -- ", ''.join(old_transpose), old_entropy, best_encoding_entropy, best_transformed

  return best_transformed