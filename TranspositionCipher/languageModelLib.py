#!/usr/bin/python

import math
import re
from os import path, walk

def getSampleTextfiles():
  for root, subFolders, files in walk("./textSamples"):
    for filename in files:
      if (filename.endswith(".txt")):
        yield path.join(root, filename)

def readAndSimplifyFiles(filenames, char_list):
  count = 0
  for filename in filenames:
    if (count > 10): break
    f = open(filename, "r")
    for raw_line in f:
      sentences = re.split('\\.|\\?|\\!', raw_line)
      for sentence in sentences:
        filtered_sentence = [x for x in list(sentence.upper()) if x in char_list]
        if (len(filtered_sentence) == 0): continue
        yield ''.join(filtered_sentence)
    count += 1

def buildModel(filtered_sentences, grams = 5):
  hist = {'': 0}
  hist_known_words = {}
  totalWords = 0
  
  for sentence in filtered_sentences:
    sentence_plus = '<' + sentence + '>'
    sentence_length = len(sentence_plus)
    
    for i in range(0, sentence_length):
      hist[''] += 1
      for j in range(1, grams + 1):
        if (i + j > sentence_length): continue
        gram = sentence_plus[i:(i+j)]
        if (gram not in hist): hist[gram] = 0
        hist[gram] += 1
    
    words = sentence.replace("  ", " ").split(" ")
    for word in words:
      if word not in hist_known_words: hist_known_words[word] = 0
      hist_known_words[word] += 1
      totalWords += 1
    
    if ('<' not in hist): hist['<'] = 0
    hist['<'] += 1
  
  truncated_hist_known_words = {k: v for k, v in hist_known_words.items() if v > 1}
  
  return hist, truncated_hist_known_words, totalWords

def outputModel(model, filename):
  hist, truncated_hist_known_words, totalWords = model
  f = open(filename, "w")
  f.write(str(len(hist)) + "\t" + str(len(truncated_hist_known_words)) + "\t" + str(totalWords) + "\n")
  
  for chars in hist: f.write(chars + "\t" + str(hist[chars]) + "\n")
  for word in truncated_hist_known_words: f.write(word + "\t" + str(truncated_hist_known_words[word]) + "\n")
  f.close()

def readInModel(filename):
  f = open(filename, "r")
  firstLine = f.readline().split("\t")
  (char_grams_count, known_words_count, totalWords) = map(lambda x: int(x), firstLine)
  hist = {}
  for i in range(0, char_grams_count):
    ngram, count_str = f.readline().split("\t")
    hist[ngram] = int(count_str)
  
  hist_known_words = {}
  for i in range(0, known_words_count):
    word, count_str = f.readline().split("\t")
    hist_known_words[word] = int(count_str)
  
  return hist, hist_known_words, totalWords

potential_word_pattern = re.compile('[ABCDEFGHIJKLMNOPQRSTUVWXYZ]+')

# use a unigram (bag of characters) model to assign probabilities to the space placement 
def entropyOfSpacePlacement(text, model, smoothingConstant = 50.0):
  ngram_model, hist_known_words, total_words = model
  probabilityOfASpace = float(smoothingConstant + ngram_model.get(" " , 0)) / (smoothingConstant + ngram_model.get("", 0))
  probabilityOfANonSpace = float(1 - probabilityOfASpace) / 26
  countProposedChar = list(text).count(" ")
  countOtherChars = len(text) - countProposedChar
  ent = -1 * countProposedChar * math.log(probabilityOfASpace) - countOtherChars * math.log(probabilityOfANonSpace)
  return ent
        
# Find the probability of seeing an unknown word using the letter ngram model
def entropyOfAnUnknownWord(word, model, smoothingConstant, letterGrams):
  ngram_model, hist_known_words, total_words = model
  entropy = 0.0
  char_ix = 0
  while (char_ix < len(word)):
    probability = 1.0 / 28
    for nth_gram in range(1, letterGrams + 1):
      if (char_ix + 1 - nth_gram < 0): break
      ngram_text = word[(char_ix + 1 - nth_gram):(char_ix + 1)]
      conditional_ngram_text = word[(char_ix + 2 - nth_gram):(char_ix + 1)]
      #smooth from previous
      probability = (smoothingConstant * probability + ngram_model.get(ngram_text, 0)) / (smoothingConstant + ngram_model.get(conditional_ngram_text, 0))
    
    entropy -= math.log(probability)
    if probability > 1:
      print entropy, probability, char_ix, nth_gram, word
      print '"' + ngram_text + '"', ngram_model.get(ngram_text, 0)
      print '"' + conditional_ngram_text + '"', ngram_model.get(conditional_ngram_text, 0)
    
    char_ix += 1
  return entropy

# Here we take the space placement as a given, break the message into words, and find the result
# right now, it's unigram on the words
def entropyOfTextWithWordsGivenSpacePlacement(text, model, smoothingConstant = 50, letterGrams = 5):
  ngram_model, hist_known_words, total_words = model
  total_known_words = sum(hist_known_words.values())
  percentage_known_words = float(total_known_words) / total_words
  
  wordList = text.replace("  ", " ").split(" ")
  
  entropy = 0.0
  
  for word in wordList:
    if (word in hist_known_words):
      known_word_prob = float(hist_known_words[word]) / total_words
      entropy -= math.log(known_word_prob) + math.log(percentage_known_words)
    else:
      # Include the probability of running into an unknown word
      entropy -= math.log(1 - percentage_known_words)
      entropy += entropyOfAnUnknownWord(word, model, smoothingConstant, letterGrams)
  
  return entropy

def entropyOfText(text, model, smoothingConstant = 50, grams = 5):
  entropy = entropyOfSpacePlacement(text, model, smoothingConstant)
  entropy += entropyOfTextWithWordsGivenSpacePlacement(text, model, smoothingConstant, grams)
  return entropy