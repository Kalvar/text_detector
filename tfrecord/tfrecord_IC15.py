import numpy as np
import scipy.io as sio
from random import shuffle

import io
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))+"/..")
from lxml import etree
import PIL.Image
import tensorflow as tf
import tfrecord_utils
ROOT_DIR = os.path.dirname(os.path.abspath(__file__+"/.."))

flags = tf.app.flags
flags.DEFINE_string('data_dir', os.path.join(ROOT_DIR,'train_data/2015/'), 'Root directory to raw pet dataset, like /startdt_data/HDA_Dataset_V1.3/VOC_fmt_training_fisheye')
flags.DEFINE_string('output_dir', os.path.join(ROOT_DIR,'train_data/2015/'), 'Path to directory to output TFRecords, like models/hda_cam_person_fisheye')
FLAGS = flags.FLAGS


def dict_to_tf_example(img_path, labels, sp):
  """Convert XML derived dict to tf.Example proto.
  Notice that this function normalizes the bounding box coordinates provided
  by the raw data.
  Args:
    data: dict holding PASCAL XML fields for a single image (obtained by
      running dataset_util.recursive_parse_xml_to_dict)
    label_map_dict: A map from string label names to integers ids.
    image_subdirectory: String specifying subdirectory within the
      Pascal dataset (here only head available) directory holding the actual image data.
    ignore_difficult_instances: Whether to skip difficult instances in the
      dataset  (default: False).
  Returns:
    example: The converted tf.Example.
  Raises:
    ValueError: if the image pointed to by data['filename'] is not a valid JPEG
  """
  with tf.gfile.GFile(img_path, 'rb') as fid:
    encoded_jpg = fid.read()

  encoded_jpg_io = io.BytesIO(encoded_jpg)
  image = PIL.Image.open(encoded_jpg_io)
  if image.format != 'JPEG':
    raise ValueError('Image format not JPEG')
  if image.mode != 'RGB':
    image = image.convert('RGB')

  width, height = image.size

  x0 = []
  y0 = []
  x1 = []
  y1 = []
  x2 = []
  y2 = []
  x3 = []
  y3 = []
  classes = []

  for label in labels:
    _x0, _y0, _x1, _y1,_x2, _y2, _x3, _y3, txt = label.split(sp)[:9]

    if "###" in txt:
        continue

    try:
        _x0 = int(_x0)
    except:
        _x0 = int(_x0[1:])

    _y0, _x1, _y1,_x2, _y2, _x3, _y3 = [int(p) for p in [_y0, _x1, _y1,_x2, _y2, _x3, _y3]]

    y0.append(_y0 / height)
    x0.append(_x0 / width )
    y1.append(_y1 / height)
    x1.append(_x1 / width )
    y2.append(_y2 / height)
    x2.append(_x2 / width )
    y3.append(_y3 / height)
    x3.append(_x3 / width )
    classes.append(1)

  if len(y0) == 0:
    return None

  example = tf.train.Example(features=tf.train.Features(feature={
      'image/encoded': tfrecord_utils.bytes_feature(encoded_jpg),
      'image/format': tfrecord_utils.bytes_feature('jpg'.encode('utf8')),
      'image/object/bbox/y0': tfrecord_utils.float_list_feature(y0),
      'image/object/bbox/x0': tfrecord_utils.float_list_feature(x0),
      'image/object/bbox/y1': tfrecord_utils.float_list_feature(y1),
      'image/object/bbox/x1': tfrecord_utils.float_list_feature(x1),
      'image/object/bbox/y2': tfrecord_utils.float_list_feature(y2),
      'image/object/bbox/x2': tfrecord_utils.float_list_feature(x2),
      'image/object/bbox/y3': tfrecord_utils.float_list_feature(y3),
      'image/object/bbox/x3': tfrecord_utils.float_list_feature(x3),
      'image/object/class/label': tfrecord_utils.int64_list_feature(classes),
  }))
  return example


def create_tf_record(output_path, data_dir):
    """Creates a TFRecord file from examples.
    Args:
        output_filename: Path to where output file is saved.
        label_map_dict: The label map dictionary.
        annotations_dir: Directory where annotation files are stored.
        image_dir: Directory where image files are stored.
        examples: Examples to parse and save to tf record.
    """
    # Train_tfrecord
    writer_train = tf.python_io.TFRecordWriter(output_path + "train_IC15.record")

    train_list = os.listdir(data_dir + "train")
    train_list = [l[:-4] for l in train_list if "jpg" in l]

    train_size = len(train_list)

    print ('{} training examples.', len(train_list))
    for n, i in enumerate(train_list):
        if n % 100 == 0:
            print ('On image {} of {}'.format(n, train_size), end='\r')

        img_file = data_dir + "train/%s.jpg" % (i)
        label_file = open(data_dir + "train/gt_%s.txt" % (i))
        label_file = label_file.readlines()

        tf_example = dict_to_tf_example(img_file, label_file, ",")
        if tf_example is not None:
            writer_train.write(tf_example.SerializeToString())

    writer_train.close()

    # Valid_tfrecord
    writer_val = tf.python_io.TFRecordWriter(output_path + "val_IC15.record")

    val_list = os.listdir(data_dir + "test")
    val_list = [l[:-4] for l in val_list if "jpg" in l]

    val_size = len(val_list)

    print ('{} valid examples.', val_size)
    for n, i in enumerate(val_list):
        if n % 100 == 0:
            print ('On image {} of {}'.format(n, val_size), end='\r')

        img_file = data_dir + "test/%s.jpg" % (i)
        label_file = open(data_dir + "test/gt_%s.txt" % (i))

        tf_example = dict_to_tf_example(img_file, label_file, ",")
        if tf_example is not None:
            writer_val.write(tf_example.SerializeToString())

    writer_val.close()


# TODO: Add test for pet/PASCAL main files.
def main(_):
    data_dir = FLAGS.data_dir
    print ("Generate data for model !")

    if not os.path.exists(FLAGS.output_dir):
        os.makedirs(FLAGS.output_dir)

    create_tf_record(FLAGS.output_dir, data_dir)

if __name__ == '__main__':
  tf.app.run()