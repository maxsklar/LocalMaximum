#!/usr/bin/python

import random
import math
import re
import languageModelLib

Characters = ' ABCDEFGHIJKLMNOPQRSTUVWXYZ'
NumCharacters = len(Characters)
EndSentencePunct = list('.?!')

def randomTranspose(numberToSelect):
  copy = list(Characters)
  random.shuffle(copy)
  return copy[:numberToSelect]

# In this case, we already know which character is the space
def randomTransposeGivenSpace(charsInMessage, space):
  copy = list(Characters)
  random.shuffle(copy)
  
  if (space in charsInMessage):
    space_ix = charsInMessage.find(space)
    space_ix_in_copy = copy.index(" ")
    copy = transposeIndecies(copy, space_ix_in_copy, space_ix)
  
  numberToSelect = len(charsInMessage)
  return ''.join(copy[:numberToSelect])

# Choose a random integer from 0 to maxInt-1, not allowing the set of forbidden ints
def chooseInt(maxInt, forbiddenSet):
  remainingSet = set(range(0, maxInt)) - forbiddenSet
  if (len(remainingSet) == 0): return -1
  ix = random.randint(0, len(remainingSet) - 1)
  return list(remainingSet)[ix]

def randomSingleCharTransposeNotSpace(transpose):
  space_ix = transpose.find(" ")
  
  L = len(transpose)
  first_ix = chooseInt(L, set([space_ix]))
  first_char = transpose[first_ix]
  
  second_ix = chooseInt(NumCharacters, set([Characters.find(" "), Characters.find(first_char)]))
  second_char = Characters[second_ix]
  
  if (second_char in transpose):
    index_to_swap = transpose.index(second_char)
    return transposeIndecies(transpose, first_ix, index_to_swap)
  
  copy = list(transpose)
  copy[first_ix] = second_char
  
  return ''.join(copy)
    
def generateAllSingleCharTransposes(transpose):
  allTransposes = []
  L = len(transpose)
  space_ix = transpose.find(" ")
  for first_ix in range(0, L):
    if (first_ix == space_ix): continue
    for second_ix in range(0, NumCharacters):
      second_char = Characters[second_ix]
      if (second_char == " "): continue
      
      if (second_char in transpose):
        index_to_swap = transpose.index(second_char)
        if (index_to_swap <= first_ix): continue
        allTransposes.append(''.join(transposeIndecies(transpose, first_ix, index_to_swap)))
      else:
        copy = list(transpose)
        copy[first_ix] = second_char
        allTransposes.append(''.join(copy))
  return allTransposes

def generateAllDoubleTransposes(transpose):
  singleTransposes = generateAllSingleCharTransposes(transpose)
  
  allTransposes = []
  
  for singleTranspose in singleTransposes:
    doubleTranspose = generateAllSingleCharTransposes(singleTranspose)
    if (doubleTranspose == transpose): continue
    allTransposes.append(doubleTranspose)
  
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

def decodeMessageTrialMarkov(message, model, steps, knownSpace = None):
  charsInMessageList = list(set(message))
  charsInMessageList.sort()
  charsInMessage = ''.join(charsInMessageList)

  space = knownSpace if (knownSpace) else chooseSpacePlacement(message, model)

  old_transpose = randomTransposeGivenSpace(charsInMessage, space)
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
        remainingTransposes = generateAllDoubleTransposes(old_transpose)

  return old_transpose, old_transformed, old_entropy

def decodeMessage(message, model, trials, knownSpace = None):
  best_encoding_entropy = float("inf")
  best_transpose = None
  best_transformed = None
  
  for trial in range(0, trials):
    result = decodeMessageTrialMarkov(message, model, 1000, knownSpace)
    
    old_transpose, old_transformed, old_entropy = result
    
    if (old_entropy < best_encoding_entropy):
      # Trial is accepted
      best_encoding_entropy = old_entropy
      best_transpose = old_transpose
      best_transformed = old_transformed
    
    print "TRIAL " + str(trial), old_transformed, " -- ", ''.join(old_transpose), old_entropy, best_encoding_entropy, best_transformed

  return best_transformed

######################
### Brute Force Search

def advanceTransposeList(currentTransposeList, space_ix):
  advancing_ix = len(currentTransposeList) - 1
  
  while advancing_ix >= 0:
    if (advancing_ix == space_ix):
      advancing_ix -= 1
      continue
    
    currentTransposeList[advancing_ix] += 1
    
    if (currentTransposeList[advancing_ix] == len(Characters)):
      currentTransposeList[advancing_ix] = 0
      advancing_ix -= 1
    else: return True
  return False
  
def transposeListToTranspose(tlist):
  return ''.join(map(lambda x: Characters[x], tlist))

def isValidTranspose(tlist, space_ix):
  # Check for duplicates
  if (len(tlist) != len(set(tlist))): return False
  
  # Check on known space
  if (space_ix != -1):
    if (tlist[space_ix] != 0): return False
  elif (0 in tlist):
    return False
    
  return True
  
def decodeMessageBruteForce(message, model, knownSpace = None):
  charsInMessageList = list(set(message))
  charsInMessageList.sort()
  charsInMessage = ''.join(charsInMessageList)
  
  print "CHARS TO DESCRAMBLE: " + charsInMessage
  
  space_ix = charsInMessage.find(knownSpace)
  
  best_encoding_entropy = float("inf")
  best_transpose = None
  best_transformed = None
  
  tlist = [0] * len(charsInMessage)
  
  for i in range(0, len(charsInMessage)):
    if (space_ix == -1): tlist[i] = i + 1
    elif (i < space_ix): tlist[i] = i + 1
    elif (i == space_ix): tlist[i] = 0
    elif (i > space_ix): tlist[i] = i
  
  trial = 0
  while True:
    if (isValidTranspose(tlist, space_ix)):
      new_transpose = transposeListToTranspose(tlist)
      new_transformed = transformText(message, charsInMessage, new_transpose)
      new_entropy = languageModelLib.entropyOfText(new_transformed, model)
      
      if (trial % 10000 == 0): print "TRIAL: " + str(trial) + " --- " + new_transpose
      
      trial += 1

      if (new_entropy < best_encoding_entropy):
        best_transformed = new_transformed
        best_transpose = new_transpose
        best_encoding_entropy = new_entropy
        
        print "NEW BEST ON TRIAL " + str(trial), best_transpose, "---", best_encoding_entropy, "---", best_transformed 
      
    shouldContinue = advanceTransposeList(tlist, space_ix)
    if (not shouldContinue): break
  return best_transformed
    