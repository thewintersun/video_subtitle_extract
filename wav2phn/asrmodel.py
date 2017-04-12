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
import codecs

FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_float('gpu_memory_fraction', 0.9, 'gpu占用内存比例')

logger = logging.getLogger(__name__)


class AsrModel:
  """
    使用声学模型的训练结果，
    加载声学模型，
    完成从特征到音素的转换
  """

  def __init__(self, model_dir, vscope, is_use_gpu=1, gpu_id="3"):
    """初始化

    Args:
      model_dir: tensorflow声学模型的模型所在的目录

    """
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu_id
    self.is_use_gpu = is_use_gpu
    self.__batch_size = 30
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

    label_count_file = os.path.join(model_dir, "label.counts.map")
    label_count_list = self.__read_label_count(label_count_file)
    normal_label_count_list = self.__normalize_label_count(label_count_list)
    #计算出来的label个数的加权值，在每一轮网络出来的每一行减去这个值
    self.__tf_label_count_logits = tf.constant(normal_label_count_list, dtype=tf.float32)


    self.__feature_cols = self.__config_dict["feature_cols"]  # 一帧包含多少个特征数字
    self.__num_classes = self.__config_dict["label_num"] + 1  # label的个数 + 1
    

    # 创建session
    self.graph = tf.Graph()
    with self.graph.as_default():
      self.__construct_graph(vscope)  # 构建模型的图结构
      self.__saver = tf.train.Saver()
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    self.__session = tf.Session(graph=self.graph,config=config)
    
    
    self.__load_model(model_dir)


  def __read_label_count(self, label_count_file):
    """
    读取label_count的文件，读入list. label为0的count放到最后。
    这个文件的行数就是label个数+1
    为了和tensorflow的进ctc的列对应上， 把0调整到最后一个。
    Args:
      label_count_file: 读入文件

    Returns:返回list

    """

    label_count_list = []
    zero_count = 0
    with codecs.open(label_count_file, 'r', "utf-8") as fr:
      for line in fr:
        label_index = int(line.split()[0])
        label_count = int(line.split()[1])
        if label_index == 0:
          zero_count = label_count
          continue
        label_count_list.append(label_count)
      label_count_list.append(zero_count)
    return label_count_list

  def __normalize_label_count(self, label_count_list):
    """
    将label种类个数统计的list中的数据进行处理， 主要操作是进行除以sum的计算，计算log等
    计算完成的结果， 将在每次网络出来的结果的label分类的概率上做加权处理
    Args:
      label_count_list: label个数的list

    Returns: 归一label之后的list，后续用于对网络出来的结果做加权处理

    """

    prior_cutoff = 1e-10      # 一个很小的数
    flt_max = 3.402823466e+38 # 浮点数最大值

    dim = len(label_count_list)
    mask_list = [0] * dim
    num_cutoff = 0

    #检查每一个count，是否有小于设定的最小值的
    for i in range(len(label_count_list)):
      if label_count_list[i] < prior_cutoff:
        label_count_list[i] = prior_cutoff
        mask_list[i] = flt_max/2
        num_cutoff += 1
    if num_cutoff > 0:
      logger.info("%d out of %d classes have counts  lower than %f" %(num_cutoff, dim, prior_cutoff))

    label_count_sum = sum(label_count_list)
    for i in range(len(label_count_list)):
      label_count_list[i] *= (1.0 / label_count_sum)
      label_count_list[i] = math.log(label_count_list[i])
      label_count_list[i] += (1.0 * mask_list[i])
    return label_count_list


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
    print("%s, global_step = %d"%(ckpt.model_checkpoint_path, global_step))


  def __construct_graph(self, vscope):
    """构建tf的图结构， 这个图结构必须和训练的时候结构一样，
      否则读取的模型，无法加载

    """
    batch_size = self.__batch_size
    if self.is_use_gpu == 0:
    with tf.device('/cpu:0'):
      num_layers = self.__hyper_parameters.num_layers
      num_hidden = self.__hyper_parameters.num_hidden
      self.__seq_len = tf.placeholder(tf.int32, [batch_size])
      self.__feature_area = tf.placeholder(tf.float32,
                                         [batch_size, None, self.__feature_cols])

      seq_len = tf.reshape(self.__seq_len, [batch_size])


      with tf.variable_scope(vscope):
        ctc_in = asr_utils.inference(num_hidden, num_layers, self.__num_classes,
                                   self.__feature_area, seq_len, batch_size)

      self.__ctc_decoded, _ = tf.nn.ctc_greedy_decoder(ctc_in, seq_len)
    else:
      num_layers = self.__hyper_parameters.num_layers
      num_hidden = self.__hyper_parameters.num_hidden
      self.__seq_len = tf.placeholder(tf.int32, [batch_size])
      self.__feature_area = tf.placeholder(tf.float32,
                                       [batch_size, None, self.__feature_cols])

      seq_len = tf.reshape(self.__seq_len, [batch_size])


      with tf.variable_scope(vscope):
        ctc_in = asr_utils.inference(num_hidden, num_layers, self.__num_classes,
                                   self.__feature_area, seq_len, batch_size)

      self.__ctc_decoded, _ = tf.nn.ctc_greedy_decoder(ctc_in, seq_len)

  def feature_to_matrix(self, feature):
    seq_len = feature.shape[0]
    logits_result = self.__session.run([self.__logits],
                                       feed_dict={self.__seq_len: [seq_len],
                                                  self.__feature_area: feature})
    return logits_result

  def feature_to_greedy_ctc_decode(self, feature, seq_len):
    #seq_len = feature.shape[0]
    if len(seq_len) != self.__batch_size:
      print("seq_len not equal to batchsize: %d" % len(seq_len))
      return ""

    greedy_decode = self.__session.run([self.__ctc_decoded[0]], feed_dict={self.__seq_len: seq_len, self.__feature_area: feature})

    result_list = []
    for i in range(self.__batch_size):
      result_list.append([])

    ids = greedy_decode[0].values
    chars = [self.__unit_dict[i + 1] for i in ids]
    j = 0
    for i in range(greedy_decode[0].indices.shape[0]):
      batch_index = greedy_decode[0].indices[i][0]
      result_list[batch_index].append(chars[j])
      j += 1
    return result_list







if __name__ == "__main__":
  logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s",
                      level=logging.INFO)




