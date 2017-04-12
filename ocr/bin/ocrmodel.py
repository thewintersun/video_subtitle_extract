# coding=utf-8

import logging
import math
import os
import yaml
import cv2
import codecs
import tensorflow as tf
import numpy as np
import ocr_utils

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_float('gpu_memory_fraction', 0.7, 'gpu占用内存比例')

logger = logging.getLogger(__name__)


class OCRModel:
  """
    使用声学模型的训练结果，
    加载声学模型，
    完成从特征到音素的转换
  """


  def __init__(self, model_dir, is_use_gpu=1, gpu_id="3"):
    """初始化

    Args:
      model_dir: tensorflow声学模型的模型所在的目录

    """
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu_id
    self.is_use_gpu = is_use_gpu
    self.__batch_size = 50
    self.__unit_dict = {}
    units_file = os.path.join(model_dir,"units.txt")
    with codecs.open(units_file, 'r','utf-8') as unit_reader:
      for line in unit_reader:
        chinese_char,unit_id = line.strip().split()
        self.__unit_dict[int(unit_id)] = chinese_char

    self.graph = tf.Graph()
    with self.graph.as_default():
      self.__construct_graph()  # 构建模型的图结构
      self.__saver = tf.train.Saver()

    gpu_options = tf.GPUOptions(
    per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    config = tf.ConfigProto(gpu_options=gpu_options)
    #config.gpu_options.allow_growth = True
    
    self.__session = tf.Session(graph=self.graph, config=config)
 
    self.__load_model(model_dir)

    

  def __read_config(self, config_file):
    """读取和模型相关的一些参数信息， 比如训练的时候label的个数
    
    Args:
      config_file: 配置文件的路径

    Return:
      包含配置信息的dict

    """
    config_dict = {}
    with codecs.open(config_file, 'r', "utf-8") as fr:
      for line in fr:
        words = line.strip().split(" ")
        if words[0] == "label_num":
          config_dict["label_num"] = int(words[1])
        if words[0] == "feature_cols":
          config_dict["feature_cols"] = int(words[1])

    return config_dict


  def __load_model(self, model_path):
    """
    读取已经训练好的模型的文件，
    Args:
      model_path:  模型的路径.

    Returns:

    """

    ckpt = tf.train.get_checkpoint_state(model_path)
    self.__saver.restore(self.__session, ckpt.model_checkpoint_path)
    global_step = int(ckpt.model_checkpoint_path.split('/')[-1].split('-')[-1])
    logger.info("从%s载入模型参数, global_step = %d",
                ckpt.model_checkpoint_path, global_step)


  def __construct_graph(self):
    """构建tf的图结构， 这个图结构必须和训练的时候结构一样，
      否则读取的模型，无法加载

    """
    batch_size = self.__batch_size
    if self.is_use_gpu == 0:
      with tf.device('/cpu:0'):
        self.__seq_len = tf.placeholder(tf.int32, [batch_size],name="ph_seq_len")
        self.__feature_area = tf.placeholder(tf.float32,
                                         [None, 38],name="ph_feature_area")
        feature_area = tf.reshape(self.__feature_area, [batch_size, -1, 38])
        seq_len = tf.reshape(self.__seq_len, [batch_size])
        feature_area = tf.cast(feature_area, tf.float32) * (1. / 255) - 0.5
        with tf.variable_scope("inference"):
          ctc_in = ocr_utils.inference(feature_area, seq_len, batch_size)

        self.__ctc_decoded, _ = tf.nn.ctc_greedy_decoder(ctc_in, seq_len)
    else:
      self.__seq_len = tf.placeholder(tf.int32, [batch_size],name="ph_seq_len")
      self.__feature_area = tf.placeholder(tf.float32,
                                       [None, 38],name="ph_feature_area")
      feature_area = tf.reshape(self.__feature_area, [batch_size, -1, 38])
      seq_len = tf.reshape(self.__seq_len, [batch_size])
      feature_area = tf.cast(feature_area, tf.float32) * (1. / 255) - 0.5
      with tf.variable_scope("inference"):
        ctc_in = ocr_utils.inference(feature_area, seq_len, batch_size)

      self.__ctc_decoded, _ = tf.nn.ctc_greedy_decoder(ctc_in, seq_len)
    



  def pic_to_char(self, picfile):
    if not os.path.exists(picfile):
      return []
    feature = self.img2data(picfile.encode('utf-8'))

    seq_len = feature.shape[0]
    decode_result = self.__session.run(self.__ctc_decoded[0],
                                       feed_dict={self.__seq_len: [seq_len],
                                                  self.__feature_area: feature})
    ids = decode_result.values
    chars = [self.__unit_dict[i] for i in ids]
    return chars

  def piclist_to_char(self, pic_feature_list, seq_len_list):

    decode_result = self.__session.run(self.__ctc_decoded[0],
                                       feed_dict={self.__seq_len: seq_len_list,
                                                  self.__feature_area: pic_feature_list})

    result_list = []
    for i in range(self.__batch_size):
      result_list.append([])

    ids = decode_result.values
    chars = [self.__unit_dict[i] for i in ids]
    j = 0
    for i in range(decode_result.indices.shape[0]):
      batch_index = decode_result.indices[i][0]
      result_list[batch_index].append(chars[j])
      j += 1

    return result_list



if __name__ == "__main__":
  logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s",
                      level=logging.INFO)




