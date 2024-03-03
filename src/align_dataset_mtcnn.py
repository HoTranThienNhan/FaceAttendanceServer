"""Performs face alignment and stores face thumbnails in the output directory."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os
import argparse
import tensorflow as tf
import numpy as np
import src.align.detect_face
import random
from time import sleep
from PIL import Image

class ImageClass():
    "Stores the paths to images for a given class"
    def __init__(self, name, image_paths):
        self.name = name
        self.image_paths = image_paths
  
    def __str__(self):
        return self.name + ', ' + str(len(self.image_paths)) + ' images'
  
    def __len__(self):
        return len(self.image_paths)

def get_image_paths(facedir):
    image_paths = []
    if os.path.isdir(facedir):
        images = os.listdir(facedir)
        image_paths = [os.path.join(facedir,img) for img in images]
    return image_paths

def get_dataset(path, has_class_directories=True):
    dataset = []
    path_exp = os.path.expanduser(path)
    classes = [path for path in os.listdir(path_exp) \
                    if os.path.isdir(os.path.join(path_exp, path))]
    classes.sort()
    nrof_classes = len(classes)
    for i in range(nrof_classes):
        class_name = classes[i]
        facedir = os.path.join(path_exp, class_name)
        image_paths = get_image_paths(facedir)
        dataset.append(ImageClass(class_name, image_paths))
  
    return dataset

def to_rgb(img):
    w, h = img.shape
    ret = np.empty((w, h, 3), dtype=np.uint8)
    ret[:, :, 0] = ret[:, :, 1] = ret[:, :, 2] = img
    return ret


#############################################
def main(args):
    sleep(random.random())
    output_dir = os.path.expanduser(args.output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Store some git revision info in a text file in the log directory
    # src_path,_ = os.path.split(os.path.realpath(__file__))
    # facenet.store_revision_info(src_path, output_dir, ' '.join(sys.argv))
    dataset = get_dataset(args.input_dir)

    print('Creating networks and loading parameters')

    with tf.Graph().as_default():
        sess = tf.compat.v1.Session()
        with sess.as_default():
            pnet, rnet, onet = src.align.detect_face.create_mtcnn(sess, None)

    minsize = 20 # minimum size of face
    threshold = [ 0.6, 0.7, 0.7 ]  # three steps's threshold
    factor = 0.709 # scale factor

    # Add a random key to the filename to allow alignment using multiple processes
    random_key = np.random.randint(0, high=99999)
    bounding_boxes_filename = os.path.join(output_dir, 'bounding_boxes_%05d.txt' % random_key)


    with open(bounding_boxes_filename, "w") as text_file:
        total_images = 0
        successfully_aligned_images = 0
        if args.random_order:
            random.shuffle(dataset)
        for cls in dataset:
            if args.input_cls and args.input_cls != cls.name:
                continue
            output_class_dir = os.path.join(output_dir, cls.name)   # Dataset/processed\<class name>
            # create output directory if not exists (create <class name> in Dataset\processed)
            if not os.path.exists(output_class_dir):
                os.makedirs(output_class_dir)
                if args.random_order:
                    random.shuffle(cls.image_paths)
            for image_path in cls.image_paths:      # image_path means each image in user folder        
                total_images += 1
                filename = os.path.splitext(os.path.split(image_path)[1])[0]    # image file name after removing extension part
                output_filename = os.path.join(output_class_dir, filename+'.png')   # Dataset/processed\<class name>\<file name>.png
                # create file name in output folder if file not exists in real 
                if not os.path.exists(output_filename):
                    try:
                        import imageio.v2
                        img = imageio.v2.imread(image_path)
                    except (IOError, ValueError, IndexError) as e:
                        errorMessage = '{}: {}'.format(image_path, e)
                        print(errorMessage)
                    else:
                        # color image usually has 3 dimensions (ndim = 3)
                        if img.ndim<2:
                            print('Unable to align "%s"' % image_path)
                            text_file.write('%s\n' % (output_filename))
                            continue
                        if img.ndim == 2:
                            # img.ndim from 2 to 3
                            img = to_rgb(img)
                        img = img[:,:,0:3]

                        bounding_boxes, _ = src.align.detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold, factor)
                        num_faces = bounding_boxes.shape[0]    # bounding_boxes.shape = (1, 5) => bounding_boxes.shape[0] = 1 (one face)
                        if num_faces > 0:
                            det = bounding_boxes[:,0:4]  # a 2-dimension of 4 points of bounding box in coordinate
                            det_arr = []
                            img_size = np.asarray(img.shape)[0:2]   # width * height

                            if num_faces > 1:   # if more than one face in the image
                                if args.detect_multiple_faces:
                                    for i in range(num_faces):
                                        det_arr.append(np.squeeze(det[i]))
                                else:
                                    bounding_box_size = (det[:,2]-det[:,0])*(det[:,3]-det[:,1])
                                    img_center = img_size / 2
                                    offsets = np.vstack([ (det[:,0]+det[:,2])/2-img_center[1], (det[:,1]+det[:,3])/2-img_center[0] ])
                                    offset_dist_squared = np.sum(np.power(offsets,2.0),0)
                                    index = np.argmax(bounding_box_size-offset_dist_squared*2.0) # some extra weight on the centering
                                    det_arr.append(det[index,:])
                            else:
                                # remove 1 dimension of det and pushing to det_arr
                                det_arr.append(np.squeeze(det))

                            # enumerate: ['a', 'b'] => [(0, 'a'), (1, 'b')]
                            for i, det in enumerate(det_arr):
                                det = np.squeeze(det)
                                bb = np.zeros(4, dtype=np.int32)    # create bounding box coordinates
                                # pad the bounding box with a margin/2
                                bb[0] = np.maximum(det[0]-args.margin/2, 0)     # args.margin = 32
                                bb[1] = np.maximum(det[1]-args.margin/2, 0)
                                bb[2] = np.minimum(det[2]+args.margin/2, img_size[1])      # img_size[1]: height
                                bb[3] = np.minimum(det[3]+args.margin/2, img_size[0])      # img_size[0]: width
                                
                                cropped_img = img[bb[1]:bb[3],bb[0]:bb[2],:]
                                cropped_img = Image.fromarray(cropped_img)
                                # resize image to size 160*160
                                scaled = cropped_img.resize((args.image_size, args.image_size), Image.BILINEAR)    
                                successfully_aligned_images += 1

                                filename_base, file_extension = os.path.splitext(output_filename)
                                if args.detect_multiple_faces:
                                    saved_output_filename = "{}_{}{}".format(filename_base, i, file_extension)
                                else:
                                    # if detect ony one face
                                    # saved_ouput_filename is also output_filename (Dataset/processed\<class name>\<file name>.png)
                                    saved_output_filename = "{}{}".format(filename_base, file_extension)
                                # push scaled image (after aligning face) to output file
                                imageio.imwrite(saved_output_filename, scaled)
                                # store bounding boxes coordinates to bounding boxes text file
                                text_file.write('%s %d %d %d %d\n' % (saved_output_filename, bb[0], bb[1], bb[2], bb[3]))
                        else:
                            print('Unable to align "%s"' % image_path)
                            text_file.write('%s\n' % (output_filename))

    print('Total number of images: %d' % total_images)
    print('Number of successfully aligned images: %d' % successfully_aligned_images)

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    
    parser.add_argument('input_dir', type=str, help='Directory with unaligned images.')
    parser.add_argument('input_cls', type=str, help='Class directory with unaligned images.')
    parser.add_argument('output_dir', type=str, help='Directory with aligned face thumbnails.')
    parser.add_argument('--image_size', type=int,
        help='Image size (height, width) in pixels.', default=182)
    parser.add_argument('--margin', type=int,
        help='Margin for the crop around the bounding box (height, width) in pixels.', default=44)
    parser.add_argument('--random_order', 
        help='Shuffles the order of images to enable alignment using multiple processes.', action='store_true')
    parser.add_argument('--gpu_memory_fraction', type=float,
        help='Upper bound on the amount of GPU memory that will be used by the process.', default=1.0)
    parser.add_argument('--detect_multiple_faces', type=bool,
                        help='Detect and align multiple faces per image.', default=False)
    return parser.parse_args(argv)

# if __name__ == '__main__':
#     sys.argv[1:] = [
#         'Dataset/raw',      # output directory
#         'Dataset/processed',    # input directory   
#         '--image_size', '160',      # aligned image size
#         '--margin', '32',   # margin bounding box
#         '--random_order',   # shuffling the order of aligned images
#         '--gpu_memory_fraction', '0.25'     # the amount of gpu memory
#     ]
#     main(parse_arguments(sys.argv[1:]))



# run by command:
# python src/align_dataset_mtcnn.py Dataset/raw Dataset/processed --image_size 160 --margin 32  --random_order --gpu_memory_fraction 0.25