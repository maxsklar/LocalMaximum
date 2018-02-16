#!/usr/bin/python

import random
import math
import re
from os import listdir

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

def readAndSimplifyFiles(filenames, char_list):
  for filename in filenames:
    f = open("textSamples/" + filename, "r")
    for raw_line in f:
      sentences = re.split('\\.|\\?|\\!', raw_line)
      for sentence in sentences:
        filtered_sentence = [x for x in list(sentence.upper()) if x in char_list]
        if (len(filtered_sentence) == 0): continue
        yield ''.join(filtered_sentence)

smoothingConstant = 50.0
grams = 4

def buildModel(filtered_sentences):
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
  return [hist, truncated_hist_known_words, totalWords]

potential_word_pattern = re.compile('[ABCDEFGHIJKLMNOPQRSTUVWXYZ]+')

def entropyOfText(text, model):
  ngram_model = model[0]
  hist_known_words = model[1]
  total_words = model[2]
  total_known_words = sum(hist_known_words.values())
  prob_known_words = float(total_known_words) / total_words
  
  entropy = 0.0
  
  text_plus = '<' + text + '>'
  
  # Look for known words
  known_words = {}
  unknown_words = set()
  for m in potential_word_pattern.finditer(text_plus):
    potential_word = m.group()
    if (potential_word in hist_known_words):
      known_words[m.start()] = potential_word
    else:
      unknown_words.add(m.start())
  
  char_ix = 0
  while (char_ix < len(text_plus)):
    # First see if we've reached a known word - that's a big bonus
    #if (char_ix in known_words):
    #  known_word = known_words[char_ix]
    #  known_word_prob = float(hist_known_words[known_word]) / total_words
    #  entropy += -1 * math.log(known_word_prob)
    #  # TODO(max): include probability for running into a known word vs unknown word
    #  entropy += -1 * math.log(prob_known_words)
    #  
    #  # The next char is either a " " or a ">"
    #  following_char = text_plus[char_ix + len(known_word)]
    #  if (following_char != " " and following_char != ">"): print "$$$$$$$$$$$$$$$$$$$$ ", following_char
    #  following_char_prob = float(ngram_model[following_char]) / (ngram_model[" "] + ngram_model[">"])
    # entropy += -1 * math.log(following_char_prob)
    #  char_ix += len(known_word) + 1
    #  continue
    #
    
    #if (char_ix in unknown_words):
    #  entropy += -1 * math.log(1 - prob_known_words)
      
    probability = 1.0 / 28
    for nth_gram in range(1, grams + 1):
      if (char_ix + 1 - nth_gram < 0): break
      ngram_text = text_plus[(char_ix + 1 - nth_gram):(char_ix + 1)]
      conditional_ngram_text = text_plus[(char_ix + 2 - nth_gram):(char_ix + 1)]
      #smooth from previous
      probability = (smoothingConstant * probability + ngram_model.get(ngram_text, 0)) / (smoothingConstant + ngram_model.get(conditional_ngram_text, 0))
    
    entropy +=  -1 * math.log(probability)
    if probability > 1:
      print entropy, probability, char_ix, nth_gram, text_plus
      print '"' + ngram_text + '"', ngram_model.get(ngram_text, 0)
      print '"' + conditional_ngram_text + '"', ngram_model.get(conditional_ngram_text, 0)
    
    char_ix += 1
  
  if (entropy <= 0):
    print "^^^^^^^^^", text, entropy
  return entropy

def new_text_accept(old_text, new_text, char_log_probs):
  entropy_diff = entropyOfText(new_text, char_log_probs) - entropyOfText(old_text, char_log_probs)
  prob = math.exp(entropy_diff)
  accept = prob > random.random()
  return accept

def decodeMessage(message, model, iters, trials):
  best_encoding_entropy = float("inf")
  best_transpose = None
  best_transformed = None
  
  for trial in range(0, trials):
    old_transpose = randomTranspose(Characters)
    old_transformed = transformText(message, old_transpose)
    old_entropy = entropyOfText(old_transformed, model)
    
    for i in range(0, iters):
      new_transpose = randomSingleCharTranspose(old_transpose)
      if (random.random() < 0.3): new_transpose = randomSingleCharTranspose(new_transpose)
      
      new_transformed = transformText(message, new_transpose)
      new_entropy = entropyOfText(new_transformed, model)
      
      entropy_diff = old_entropy - new_entropy
      #accept = math.exp(entropy_diff) > random.random()
      accept = entropy_diff > 0
      
      if (accept):
        old_transformed = new_transformed
        old_transpose = new_transpose
        old_entropy = new_entropy
      
      if (i % 1000 == 0):
        print "  ITER " + str(i), old_transformed, " -- ", ''.join(old_transpose), old_entropy
    
    if (old_entropy < best_encoding_entropy):
      best_encoding_entropy = old_entropy
      best_transpose = old_transpose
      best_transformed = old_transformed
    
    print "TRIAL " + str(trial), old_transformed, " -- ", ''.join(old_transpose), old_entropy, best_encoding_entropy, best_transformed

  return best_transformed

key = randomTranspose(Characters)
print "Original Key: ", key

message = "hello my name is max nice to meet you i am from new york what is your name".upper()
#message = "New York is the best".upper()
encoded_message = transformText(message, key)
print "Original Encoded Message: ", encoded_message

files = listdir("./textSamples")
training_data = readAndSimplifyFiles(files, Characters)
model = buildModel(training_data)

#hist_known_words = model[1]
#for key, value in sorted(hist_known_words.iteritems(), key=lambda (k,v): (v,k)):
#    print "%s: %s" % (key, value)
#print "total", model[2]

print "Original Message: ", message
print "Original Message Entropy: ", entropyOfText(message, model)

d = decodeMessage(encoded_message, model, 10000, 1)
print "*****"
print d