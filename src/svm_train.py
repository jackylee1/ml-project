#!/usr/bin/python

import sys
import cv2
from sklearn import svm
from scipy.cluster.vq import kmeans2, vq
import numpy

import helpers

FEATURE_TYPES = 50  # Number of clusters features are put into; thus forming kinds of features. Usually sqrt(n/2)


class Category:
    """
    This class represents one category that is encountered
    while training. It is used to calculate the bag of words
    vector, after all possible feature types are added to this
    category.
    """
    def __init__(self, label, features=[]):
        self.label = label
        self.features = features
        self.bagofwords = []

    def add_feature(self, feature):
        """Add one feature vector"""
        self.features.append(feature)

    def calc_bagofwords(self, centroids):
        """Calculate bag of words using the features
        added to an object."""
        for feature in self.features:
            labels, _ = vq(numpy.array(feature), centroids)
            bow = numpy.zeros(FEATURE_TYPES)
            for label in labels:
                bow[label] += 1
            helpers.normalize(bow)
            self.bagofwords.append(bow)


def train_routine(training_file, output_folder):
    """The main training routine.
    Input: training_file: <class>;<path to image>
    output_folder: A previous created folder where output files
    are written.
    Runs the routine: Get SURF features, calculate bag of words,
    then train the linear SVM using those.
    Then writes the required objects onto files.
    """
    if output_folder[-1] != '/':
        output_folder += '/'

    svm_file = output_folder + 'svm.txt'
    centroid_file = output_folder + 'centroids.txt'
    ids_file = output_folder + 'ids.txt'

    surf = cv2.SURF(250)
    categories = {}
    ids = {}
    id = 1
    features = []

    print "Extracting features"
    for line in open(training_file):
        try:
            category, path = line.split(';')
        except:
            print "Error: File not in proper format. Ensure: <category/class name>; <path to image of said category>"
            sys.exit(0)
        path = path.strip()

        try:
            img = cv2.imread(path)
        except Exception as e:
            print e

        keypoints, descriptors = surf.detectAndCompute(img, None)

        if not category in categories:
            categories[category] = Category(category)
            ids[category] = id
            id += 1
        categories[category].add_feature(descriptors)
        features.extend(descriptors)

    print "Calculating centroids"
    np_features = numpy.array(features)
    centroids, labels = kmeans2(np_features, FEATURE_TYPES)

    print "Forming bag of words"
    X, Y = [], []
    for category in categories:
        categories[category].calc_bagofwords(centroids)
        for bow in categories[category].bagofwords:
            X.append(bow)
            Y.append(ids[category])

    print "Fitting linear SVMs onto the bag of words"
    lin_clf = svm.LinearSVC()
    lin_clf.fit(X, Y)

    helpers.saveObject(lin_clf, svm_file)
    helpers.saveObject(centroids, centroid_file)
    helpers.saveObject(ids, ids_file)

if __name__ == "__main__":
    if(len(sys.argv) != 3):
        print "Usage: $python svm_train.py training_file output_folder"
        sys.exit(1)
    train_routine(sys.argv[1], sys.argv[2])