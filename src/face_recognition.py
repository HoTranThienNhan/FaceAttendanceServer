from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
from imutils.video import VideoStream

from flask import Response

import argparse
import src.facenet
import imutils
import os
import sys
import math
import pickle
import src.align.detect_face
import numpy as np
import cv2
import collections
from sklearn.svm import SVC

class Face_Rec:
    def main(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--path', help='Path of the video you want to test on.', default=0)
        args = parser.parse_args()

        MINSIZE = 20
        THRESHOLD = [0.6, 0.7, 0.7]
        FACTOR = 0.709
        IMAGE_SIZE = 182
        INPUT_IMAGE_SIZE = 160
        CLASSIFIER_PATH = 'Models/facemodel.pkl'
        VIDEO_PATH = args.path
        FACENET_MODEL_PATH = 'Models/20180402-114759.pb'

        # Load The Custom Classifier
        with open(CLASSIFIER_PATH, 'rb') as file:
            model, class_names = pickle.load(file)
        print("Custom Classifier, Successfully loaded")

        with tf.Graph().as_default():

            # Cai dat GPU neu co
            gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=0.6)
            sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(gpu_options=gpu_options, log_device_placement=False))

            with sess.as_default():

                # Load the model
                print('Loading feature extraction model')
                src.facenet.load_model(FACENET_MODEL_PATH)

                # Get input and output tensors
                images_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("input:0")
                embeddings = tf.compat.v1.get_default_graph().get_tensor_by_name("embeddings:0")
                phase_train_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("phase_train:0")
                embedding_size = embeddings.get_shape()[1]

                pnet, rnet, onet = src.align.detect_face.create_mtcnn(sess, "src/align")

                people_detected = set()
                person_detected = collections.Counter()

        return sess, MINSIZE, IMAGE_SIZE, INPUT_IMAGE_SIZE, pnet, rnet, onet, THRESHOLD, FACTOR, model, class_names, images_placeholder, phase_train_placeholder, embeddings, embedding_size, people_detected, person_detected

