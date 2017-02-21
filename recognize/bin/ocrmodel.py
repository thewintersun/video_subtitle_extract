# coding=utf-8

import logging
import math
import os
import yaml
import cv2
import codecs
import tensorflow as tf
import numpy as np
import asr_utils

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_float('gpu_memory_fraction', 0.9, 'gpu占用内存比例')

logger = logging.getLogger(__name__)


class OCRModel:
  """
    使用声学模型的训练结果，
    加载声学模型，
    完成从特征到音素的转换
  """


  def __init__(self, model_dir):
    """初始化

    Args:
      model_dir: tensorflow声学模型的模型所在的目录

    """
    self.__unit_dict = {}
    units_file = os.path.join(model_dir,"units.txt")
    with codecs.open(units_file, 'r','utf-8') as unit_reader:
      for line in unit_reader:
        chinese_char,unit_id = line.strip().split()
        self.__unit_dict[int(unit_id)] = chinese_char

    hpper_param_config_file = os.path.join(model_dir, "hyper_param.config")
    with codecs.open(hpper_param_config_file,'r',"utf-8") as hyper_param_file:
      self.__hyper_parameters = yaml.load(hyper_param_file.read())

    config_file_path = os.path.join(model_dir, "model.config")
    self.__config_dict = self.__read_config(config_file_path)

    self.__feature_cols = self.__config_dict["feature_cols"]  # 一帧包含多少个特征数字
    self.__num_classes = self.__config_dict["label_num"] + 1  # label的个数 + 1
    self.__construct_graph()  # 构建模型的图结构

    # 创建session
    self.__saver = tf.train.Saver()
    gpu_options = tf.GPUOptions(
      per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)
    self.__session = tf.Session(config=tf.ConfigProto(device_count={'GPU':0},gpu_options=gpu_options))
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
    with tf.device('/cpu:0'):
      num_layers = self.__hyper_parameters.num_layers
      num_hidden = self.__hyper_parameters.num_hidden
      self.__seq_len = tf.placeholder(tf.int32, [1])
      self.__feature_area = tf.placeholder(tf.float32,
                                         [None, self.__feature_cols])
      feature_area = tf.reshape(self.__feature_area, [1, -1, self.__feature_cols])
      seq_len = tf.reshape(self.__seq_len, [1])
      with tf.variable_scope("inference"):
        ctc_in = asr_utils.inference(num_hidden, num_layers, self.__num_classes,
                                   feature_area, seq_len, 1)

      self.__ctc_decoded, _ = tf.nn.ctc_greedy_decoder(ctc_in, seq_len)


  def pic_to_char(self, picfile):
    feature = self.img2data(picfile)

    seq_len = feature.shape[0]
    decode_result = self.__session.run(self.__ctc_decoded[0],
                                       feed_dict={self.__seq_len: [seq_len],
                                                  self.__feature_area: feature})
    ids = decode_result.values
    chars = [self.__unit_dict[i] for i in ids]
    return chars


  def img2data(self, img_file ):
    img = cv2.imread(img_file, -1)
    gray_img = cv2.cvtColor(img, cv2.cv.CV_BGR2GRAY)
    trans_img = np.transpose(gray_img)
    return trans_img


if __name__ == "__main__":
  logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s",
                      level=logging.INFO)




