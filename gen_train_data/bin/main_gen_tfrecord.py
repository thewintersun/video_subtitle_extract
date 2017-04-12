#coding=utf-8
import cv2
import numpy as np
import codecs
import os
import tensorflow as tf
import multiprocessing
from multiprocessing import Pool, Lock, Value  

def get_img_data(img_file):
  img = cv2.imread(img_file, -1)
  gray_img = cv2.cvtColor(img, cv2.cv.CV_BGR2GRAY)
  gray_img = np.transpose(gray_img)
  return gray_img

def get_label_data(label_str, unit_dict):
  return [unit_dict[c] for c in label_str]


def gen_tfrecord(record_file, output_tfrecord_file):
  unit_file = "../data/units.txt"
  unit_dict = {}
  with codecs.open(unit_file, 'r', 'utf-8') as fr:
    for line in fr:
      char,index = line.strip().split()
      unit_dict[char]= int(index)

  train_writer = tf.python_io.TFRecordWriter(output_tfrecord_file)

  with codecs.open(record_file, 'r', 'utf-8') as fr:
    line_index = 0
    max_cv_number = 10000
    for line in fr:
      line_index += 1
      img_file, label_char, font = line.strip().split()
      if font != "simyou.ttf" and font != "song-bold.ttf":
        #在某个特定的字体下才生成数据
        writer = train_writer

        img_data = get_img_data(img_file)
        label_data = get_label_data(label_char, unit_dict)
        image_raw = img_data.tostring()
        rows = img_data.shape[0]
        cols = img_data.shape[1]
        example = tf.train.Example()
        
        feature = example.features.feature
        feature['height'].int64_list.value.append(rows)
        feature['width'].int64_list.value.append(cols)
        feature['image_raw'].bytes_list.value.append(image_raw)
        feature['label'].int64_list.value.extend(label_data)
        
        writer.write(example.SerializeToString())

  train_writer.close()

def gen_tfrecord_batch():
  record_dir = "./split_dir"
  tfrecord_dir = "../data/tfrecord/"

  if not os.path.exists(tfrecord_dir):
    os.mkdir(tfrecord_dir)

  pool = multiprocessing.Pool(processes = 8)
  
  for i in range(8):
    record_file = os.path.join(record_dir, "train.record." + str(i))
    print(record_file)
    tfrecord_file = os.path.join(tfrecord_dir, "train.tfrecord." + str(i))
    #gen_tfrecord(record_file, tfrecord_file)
    pool.apply_async(gen_tfrecord,[record_file, tfrecord_file])  
  pool.close()  
  pool.join()
  
if __name__ == '__main__':
  pass
  gen_tfrecord_batch()
