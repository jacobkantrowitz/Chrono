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

## This is the main driver program that runs Chrono.  

import argparse
import os
from Chrono.config import MODE
from Chrono import BuildSCATEEntities, referenceToken, utils

debug=False
## This is the driver method to run all of Chrono.
# @param INDIR The location of the directory with all the files in it.
# @param OUTDIR The location of the directory where you want all the output written.
# @param REFDIR The location of the gold standard XML files for evaluation.
# @return Anafora formatted XML files, one directory per file with one XML file in each directory.
# @return The precision and recall from comparing output results to the gold standard.
if __name__ == "__main__":
    
    ## Parse input arguments
    parser = argparse.ArgumentParser(description='Parse a directory of files to identify and normalize temporal information.')
    parser.add_argument('-i', metavar='inputdir', type=str, help='path to the input directory.', required=True)
    parser.add_argument('-x', metavar='fileExt', type=str, help='input file extension if exists. Default is and empty string', required=False, default="")
    parser.add_argument('-o', metavar='outputdir', type=str, help='path to the output directory.', required=True)
    parser.add_argument('-m', metavar='MLmethod', type=str, help='The machine learning method to use. Must be one of NN (neural network), DT (decision tree), SVM (support vector machine), NB (naive bayes, default).', required=False, default='NB')
    parser.add_argument('-w', metavar='windowSize', type=str, help='An integer representing the window size for context feature extraction. Default is 3.', required=False, default=3)
    parser.add_argument('-d', metavar='MLTrainData', type=str, help='A string representing the file name that contains the CSV file with the training data matrix.', required=False, default=False)
    parser.add_argument('-c', metavar='MLTrainClass', type=str, help='A string representing the file name that contains the known classes for the training data matrix.', required=False, default=False)
    parser.add_argument('-M', metavar='MLmodel', type=str, help='The path and file name of a pre-build ML model for loading.', required=False, default=None)
    parser.add_argument('-D', metavar='Dictionary', type=str, help='The path to dictionaries', required=False, default='./dictionary')
    parser.add_argument('-O', metavar='Mode', type=str, help='Output mode', required=False, default="SCATE")
    
    args = parser.parse_args()
    ## Now we can access each argument as args.i, args.o, args.r
    utils.initialize(in_mode=args.O)
    classifier, feats = utils.setup_ML(args.m, args.M, args.d, args.c)

    ## Get list of folder names in the input directory
    indirs = []
    infiles = []
    outfiles = []
    outdirs = []
    for root, dirs, files in os.walk(args.i, topdown = True):
       for name in dirs:
          indirs.append(os.path.join(root, name))
          infiles.append(os.path.join(root,name,name))
          outfiles.append(os.path.join(args.o,name,name))
          outdirs.append(os.path.join(args.o,name))
          if not os.path.exists(os.path.join(args.o,name)):
              os.makedirs(os.path.join(args.o,name))

    ## Pass the ML classifier through to the parse SUTime entities method.
    print("Parsing in {} mode".format(MODE))
    ## Loop through each file and parse
    for f in range(0,len(infiles)) :
        print("Parsing "+ infiles[f] +" ...")
        ## Init the ChronoEntity list
        my_chronoentities = []
        my_chrono_ID_counter = 1

        ## parse out the doctime
        doctime = utils.getDocTime(infiles[f] + ".dct")
        if(debug) : print(doctime)

        ## parse out reference tokens
        text, tokens, spans, tags, sents = utils.getWhitespaceTokens(infiles[f]+args.x)
        #my_refToks = referenceToken.convertToRefTokens(tok_list=tokens, span=spans, remove_stopwords="./Chrono/stopwords_short2.txt")
        my_refToks = referenceToken.convertToRefTokens(tok_list=tokens, span=spans, pos=tags, sent_boundaries=sents)



        ## mark all ref tokens if they are numeric or temporal
        chroList = utils.markTemporal(my_refToks)

        if(debug) :
            print("REFERENCE TOKENS:\n")
            for tok in chroList : print(tok)

        tempPhrases = utils.getTemporalPhrases(chroList, doctime)

        if(debug):
            for c in tempPhrases:
                print(c)

        chrono_master_list, my_chrono_ID_counter = BuildSCATEEntities.buildChronoList(tempPhrases, my_chrono_ID_counter, chroList, (classifier, args.m), feats, doctime)

        print("Number of Chrono Entities: " + str(len(chrono_master_list)))
        utils.write_out(chrono_list=chrono_master_list, outfile=outfiles[f])
