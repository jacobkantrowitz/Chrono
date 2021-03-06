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

## Uses Keras to build, train, a classify with a neural network

from keras.models import Sequential
from keras.layers import Dense, Dropout

import numpy as np
import csv
import string
import math
import random

## Builds and trains the neural network with the given training data
# @param train_data A CSV with the training data
# @param train_labels A CSV with the training labels
# @return The neural network classifier, pass this to keras_classify and keras_evaluate
def build_model(train_data, train_labels):
    # Import the given data
    dataset = np.loadtxt(train_data, delimiter=",",skiprows=1)
    labels = np.loadtxt(train_labels, delimiter=",")
    size = len(dataset[0,:])
    print("Size: {}".format(size))
    X = dataset[:, 0:size]
    Y = labels[:]
    
    # Build keras NN
    model = Sequential()
    model.add(Dense(size, input_shape=(size, ), activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(size, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(size*2, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(size, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    
    # Train the NN, change epochs to train longer or shorter
    model.fit(X, Y, epochs=5, batch_size=10)
    return model

## Evaluate the given model on a test set
# @param model The model to be evaluated
# @param test_data A CSV with the test data
# @param train_labels A CSV with the test labels
# @return Prints and returns the accuracy of the model on the test data
def keras_evaluate(model,test_data,test_labels):
    scores = model.evaluate(test_data, test_labels)
    print("Test data accuracy: {}".format(scores[1]*100))
    return scores

## Classfy a single sample
# @param model The model to be used
# @param predcit_data A numpy array with the sample to be classified
# @return A 0 or 1 for which class was predicted
def keras_classify(model,predict_data):
    # Keras wants a list of numpy arrays
    X = []
    X.append(list(predict_data))
    X.append(list(predict_data))
    #print("Predicting on {}".format(X))
    prediction = model.predict(X,verbose=1)
    #print("The prediction is: {}".format(np.round(prediction[0])))
    return np.round(prediction[0])
