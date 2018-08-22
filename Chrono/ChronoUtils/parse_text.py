# Copyright (c) 2018
# Amy L. Olex, Virginia Commonwealth University
# alolex at vcu.edu
#
# Luke Maffey, Virginia Commonwealth University
# maffeyl at vcu.edu
#
# Nicholas Morton,  Virginia Commonwealth University
# nmorton at vcu.edu
#
# Bridget T. McInnes, Virginia Commonwealth University
# btmcinnes at vcu.edu
#
# This file is part of Chrono
#
# Chrono is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# Chrono is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Chrono; if not, write to
#
# The Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330,
# Boston, MA  02111-1307, USA.


import copy
import re
import string

import dateutil.parser
import nltk
from Chrono import w2ny as w2n, TimePhraseEntity as tp, temporalTest as tt
from Chrono.config import DICTIONARY
from nltk import sent_tokenize, WhitespaceTokenizer
from nltk.tokenize.util import align_tokens


def getWhitespaceTokens(file_path):
    file = open(file_path, "r")
    text = file.read()
    ## Testing the replacement of all "=" signs by spaces before tokenizing.
    text = text.translate(str.maketrans("=", ' '))

    ## Tokenize the sentences
    sentences = sent_tokenize(text)

    ## Get spans of the sentences
    sent_spans = align_tokens(sentences, text)

    ## create empty arrays for white space tokens and sentence delimiters
    tokenized_text = []
    text_spans = []

    ## Loop through each sentence and get the tokens and token spans
    for s in range(0,len(sentences)):
        # get the tokens and token spans within the sentence
        toks = WhitespaceTokenizer().tokenize(sentences[s])
        span_generator = WhitespaceTokenizer().span_tokenize(sentences[s])
        rel_spans = [span for span in span_generator]

        # convert the relative spans into absolute spans
        abs_spans = []
        for start, end in rel_spans:
            abs_spans = abs_spans + [(sent_spans[s][0]+start, sent_spans[s][0]+end)]

        tokenized_text = tokenized_text + toks
        text_spans = text_spans + abs_spans

    ## Now we have the token list and the spans.  We should be able to continue finding sentnence boundaries as before
    tags = nltk.pos_tag(tokenized_text)
    sent_boundaries = [0] * len(tokenized_text)

    ## figure out which tokens are at the end of a sentence
    tok_counter = 0

    for s in range(0,len(sentences)):
        sent = sentences[s]

        if "\n" in sent:
            sent_newline = sent.split("\n")
            for sn in sent_newline:
                sent_split = WhitespaceTokenizer().tokenize(sn)
                nw_idx = len(sent_split) + tok_counter - 1
                sent_boundaries[nw_idx] = 1
                tok_counter = tok_counter + len(sent_split)

        else:
            sent_split = WhitespaceTokenizer().tokenize(sent)
            nw_idx = len(sent_split) + tok_counter - 1
            sent_boundaries[nw_idx] = 1
            tok_counter = tok_counter + len(sent_split)

    return text, tokenized_text, text_spans, tags, sent_boundaries


def getDocTime(file_path):
    file = open(file_path, "r")
    text = file.read()
    return(dateutil.parser.parse(text))


def getNumberFromText(text):
    try :
        number = w2n.word_to_num(text)
    except ValueError:
        number = isOrdinal(text)

    return number


def getMonthNumber(text):
    month_dict = {'January':1, 'February':2, 'March':3, 'April':4, 'May':5, 'June':6, 'July':7, 'August':8, 'September':9, 'October':10,'November':11, 'December':12,
                  'JANUARY':1, 'FEBRUARY':2, 'MARCH':3, 'APRIL':4, 'MAY':5, 'JUNE':6, 'JULY':7, 'AUGUST':8, 'SEPTEMBER':9, 'OCTOBER':10,'NOVEMBER':11, 'DECEMBER':12,
                  'january':1, 'february':2, 'march':3, 'april':4, 'june':6, 'july':7, 'august':8, 'september':9, 'october':10,'november':11, 'december':12,
                  'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'Jun':6, 'Jul':7, 'Aug':8, 'Sept':9, 'Sep':9, 'Oct':10,'Nov':11, 'Dec':12,
                  'jan':1, 'feb':2, 'mar':3, 'apr':4, 'jun':6, 'jul':7, 'aug':8, 'sept':9, 'sep':9, 'oct':10,'nov':11, 'dec':12,
                  'JAN':1, 'FEB':2, 'MAR':3, 'APR':4, 'JUN':6, 'JUL':7, 'AUG':8, 'SEPT':9, 'SEP':9, 'OCT':10,'NOV':11, 'DEC':12,
                  '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, '11':11, '12':12,
                  '01':1, '02':2, '03':3, '04':4, '05':5, '06':6, '07':7, '08':8, '09':9, '10':10, '11':11, '12':12}
    try:
        value = month_dict[text]
    except KeyError:
        value = 100

    return value


def getTemporalPhrases(chroList, doctime):
    #TimePhraseEntity(id=id_counter, text=j['text'], start_span=j['start'], end_span=j['end'], temptype=j['type'], tempvalue=j['value'], doctime=doctime)
    id_counter = 0

    phrases = [] #the empty phrases list of TimePhrase entities
    tmpPhrase = [] #the temporary phrases list.
    inphrase = False
    for n in range(0,len(chroList)):
        #if temporal start building a list
        #print("Filter Start Phrase: " + str(chroList[n]))
        if chroList[n].isTemporal():
            #print("Is Temporal: " + str(chroList[n]))
            if not inphrase:
                inphrase = True
            #in phrase, so add new element
            tmpPhrase.append(copy.copy(chroList[n]))
            # test to see if a new line is present.  If it is AND we are in a temporal phrase, end the phrase and start a new one.
            # if this is the last token of the file, end the phrase.
            if n == len(chroList)-1:
                if inphrase:
                    phrases.append(createTPEntity(tmpPhrase, id_counter, doctime))
                    id_counter = id_counter + 1
                    tmpPhrase = []
                    inphrase = False
            else:
                s1,e1 = chroList[n].getSpan()
                s2,e2 = chroList[n+1].getSpan()

                #if e1+1 != s2 and inphrase:
                if chroList[n].getSentBoundary() and inphrase:
                    #print("Found Sentence Boundary Word!!!!!!!!!")
                    phrases.append(createTPEntity(tmpPhrase, id_counter, doctime))
                    id_counter = id_counter + 1
                    tmpPhrase = []
                    inphrase = False


        elif chroList[n].isNumeric():
            #print("Not Temporal, but Numeric: " + str(chroList[n]))
            #if the token has a dollar sign or percent sign do not count it as temporal
            m = re.search('[#$%]', chroList[n].getText())
            if m is None:
                #print("No #$%: " + str(chroList[n]))
                #check for the "million" text phrase
                answer = next((m for m in ["million", "billion", "trillion"] if m in chroList[n].getText().lower()), None)
                if answer is None:
                    #print("No million/billion/trillion: " + str(chroList[n]))
                    if not inphrase:
                        inphrase = True
                    #in phrase, so add new element
                    tmpPhrase.append(copy.copy(chroList[n]))
            # test to see if a new line is present.  If it is AND we are in a temporal phrase, end the phrase and start a new one.
            # if this is the last token of the file, end the phrase.
            if n == len(chroList)-1:
                if inphrase:
                    phrases.append(createTPEntity(tmpPhrase, id_counter, doctime))
                    id_counter = id_counter + 1
                    tmpPhrase = []
                    inphrase = False
            else:
                s1,e1 = chroList[n].getSpan()
                s2,e2 = chroList[n+1].getSpan()

                #if e1+1 != s2 and inphrase:
                if chroList[n].getSentBoundary() and inphrase:
                    #print("Found Sentence Boundary Word!!!!!!!!!")
                    phrases.append(createTPEntity(tmpPhrase, id_counter, doctime))
                    id_counter = id_counter + 1
                    tmpPhrase = []
                    inphrase = False

        ## Now look for a linking term.  Only continue the phrase if the term is surrounded by numeric or temporal tokens.
        ## Also, only consider linking terms if we are already in a phrase.
        elif chroList[n].isLinkTerm() and inphrase:
            if (chroList[n-1].isTemporal() or chroList[n-1].isNumeric()) and (chroList[n+1].isTemporal() or chroList[n+1].isNumeric()):
                tmpPhrase.append(copy.copy(chroList[n]))

        else:
            #current element is not temporal, check to see if inphrase
            #print("Not Temporal, or numeric " + str(chroList[n]))
            if inphrase:
                #set to False, add tmpPhrase as TimePhrase entitiy to phrases, then reset tmpPhrase
                inphrase = False
                #check to see if only a single element and element is numeric, then do not add.
                if len(tmpPhrase) != 1:
                    #print("multi element phrase ")
                    phrases.append(createTPEntity(tmpPhrase, id_counter, doctime))
                    id_counter = id_counter + 1
                    tmpPhrase = []
                elif not tmpPhrase[0].isNumeric():
                    #print("not numeric: " + str(chroList[n-1]))
                    phrases.append(createTPEntity(tmpPhrase, id_counter, doctime))
                    id_counter = id_counter + 1
                    tmpPhrase = []
                elif tmpPhrase[0].isNumeric() and tmpPhrase[0].isTemporal():
                    #print("temporal and numeric: " + str(chroList[n-1]))
                    phrases.append(createTPEntity(tmpPhrase, id_counter, doctime))
                    id_counter = id_counter + 1
                    tmpPhrase = []
                else:
                    #print("Element not added: " + str(chroList[n-1]))
                    tmpPhrase = []


    return phrases


def createTPEntity(items, counter, doctime):
    start_span, tmp = items[0].getSpan()
    tmp, end_span = items[len(items)-1].getSpan()
    text = ""
    for i in items:
        text = text + ' ' + i.getText()

    return tp.TimePhraseEntity(id=counter, text=text.strip(), start_span=start_span, end_span=end_span, temptype=None, tempvalue=None, doctime=doctime)


def getRefIdx(ref_list, start_span, end_span):
    for i in range(0,len(ref_list)):
        if(overlap(ref_list[i].getSpan(),(start_span,end_span))):
            return i
    return -1


def isOrdinal(text):
    text_lower = text.lower()
    if text_lower == '1st' or text_lower== 'first': #re.search('1st|first', text_lower) is not None):
        number = 1
    elif text_lower == '2nd' or text_lower== 'second':
        number = 2
    elif text_lower == '3rd' or text_lower== 'third':
        number = 3
    elif text_lower == '4th' or text_lower== 'fourth':
        number = 4
    elif text_lower == '5th' or text_lower== 'fifth':
        number = 5
    elif text_lower == '6th' or text_lower== 'sixth':
        number = 6
    elif text_lower == '7th' or text_lower== 'seventh':
        number = 7
    elif text_lower == '8th' or text_lower== 'eighth':
        number = 8
    elif text_lower == '9th' or text_lower== 'nineth':
        number = 9
    elif text_lower == '10th' or text_lower== 'tenth':
        number = 10
    elif text_lower == '11th' or text_lower== 'eleventh':
        number = 11
    elif text_lower == '12th' or text_lower== 'twelveth':
        number = 12
    elif text_lower == '13th' or text_lower== 'thirteenth':
        number = 13
    elif text_lower == '14th' or text_lower== 'fourteenth':
        number = 14
    elif text_lower == '15th' or text_lower== 'fifteenth':
        number = 15
    elif text_lower == '16th' or text_lower== 'sixteenth':
        number = 16
    elif text_lower == '17th' or text_lower== 'seventeenth':
        number = 17
    elif text_lower == '18th' or text_lower== 'eighteenth':
        number = 18
    elif text_lower == '19th' or text_lower== 'nineteenth':
        number = 19
    elif text_lower == '20th' or text_lower== 'twentieth':
        number = 20
    elif text_lower == '21st' or text_lower== 'twenty first':
        number = 21
    elif text_lower == '22nd' or text_lower== 'twenty second':
        number = 22
    elif text_lower == '23rd' or text_lower== 'twenty third':
        number = 23
    elif text_lower == '24th' or text_lower== 'twenty fourth':
        number = 24
    elif text_lower == '25th' or text_lower== 'twenty fifth':
        number = 25
    elif text_lower == '26th' or text_lower== 'twenty sixth':
        number = 26
    elif text_lower == '27th' or text_lower== 'twenty seventh':
        number = 27
    elif text_lower == '28th' or text_lower== 'twenty eighth':
        number = 28
    elif text_lower == '29th' or text_lower== 'twenty nineth':
        number = 29
    elif text_lower == '30th' or text_lower== 'thirtieth':
        number = 30
    elif text_lower == '31st' or text_lower== 'thirty first':
        number = 31
    else:
        number = None

    return number


def overlap(sp1, sp2) :
    x=set(range(int(sp1[0]), int(sp1[1])))
    y=set(range(int(sp2[0]), int(sp2[1])))
    if list(set(x) & set(y)) != []:
        return True
    else:
        return False


def markTemporal(refToks):
    for ref in refToks:
        #mark if numeric
        ref.setNumeric(numericTest(ref.getText(), ref.getPos()))
        #mark if temporal
        ref.setTemporal(temporalTest(ref.getText()))

    ## read in the link terms dictionary
    terms = DICTIONARY["LinkTerms"]

    ## Now go through the list again and mark all linking words a, an, in, of that appear between 2 temporal and or number tokens.
    for i in range(1, len(refToks)-1):
        if (refToks[i-1].isNumeric() or refToks[i-1].isTemporal()) and (refToks[i+1].isNumeric() or refToks[i+1].isTemporal()) and (refToks[i].getText() in terms):
            refToks[i].setLinkTerm(1)

    return refToks


def numericTest(tok, pos):

    if pos == "CD":
        return True
    else:
        #remove punctuation
        tok = tok.translate(str.maketrans(string.punctuation, ' '*len(string.punctuation))).strip()

        #test for a number
        #tok.strip(",.")
        val = getNumberFromText(tok)
        #print("Testing Number: Tok: " + tok + "  Val:" + str(val))
        if val is not None:
            return True
        return False


def temporalTest(tok):
    #remove punctuation
    #tok = tok.translate(str.maketrans("", "", string.punctuation))

    #if the token has a dollar sign or percent sign it is not temporal
    m = re.search('[#$%]', tok)
    if m is not None:
        return False

    #look for date patterns mm[/-]dd[/-]yyyy, mm[/-]dd[/-]yy, yyyy[/-]mm[/-]dd, yy[/-]mm[/-]dd
    m = re.search('([0-9]{1,4}[-/][0-9]{1,2}[-/][0-9]{1,4})', tok)
    if m is not None:
        return True
    #looks for a string of 8 digits that could possibly be a date in the format 19980304 or 03041998 or 980304
    m = re.search('([0-9]{4,8})', tok)
    if m is not None:
        if tt.has24HourTime(m.group(0)):
            return True
        if tt.hasDateOrTime(m.group(0)):
            return True

    #look for time patterns hh:mm:ss
    m = re.search('([0-9]{2}:[0-9]{2}:[0-9]{2})', tok)
    if m is not None:
        return True


    if tt.hasTextMonth(tok):
        return True
    if tt.hasDayOfWeek(tok):
        return True
    if tt.hasPeriodInterval(tok):
        return True
    if tt.hasAMPM(tok):
        return True
    if tt.hasPartOfWeek(tok):
        return True
    if tt.hasSeasonOfYear(tok):
        return True
    if tt.hasPartOfDay(tok):
        return True
    if tt.hasTimeZone(tok):
        return True
    if tt.hasTempText(tok):
        return True
    if tt.hasModifierText(tok):
        return True


def calculateSpan(text, search_text):
    try:
        start_idx = text.index(search_text)
        end_idx = start_idx + len(search_text)
    except ValueError:
        return None, None

    return start_idx, end_idx