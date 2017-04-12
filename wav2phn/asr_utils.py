# coding=utf-8
# 定义模型结构, 数据预处理.
import logging

import numpy as np
import tensorflow as tf
import yaml
import re

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_integer('dev_batch_size', 10, """dev的测试的batch size""")

tf.app.flags.DEFINE_string('data_dir', '/data/1300h/',"训练数据文件夹")

tf.app.flags.DEFINE_string("train_feature_file", "train.feature",
                           """在data_dir文件下，用来训练的特征文件""")
tf.app.flags.DEFINE_string("train_feature_len_file", "train.feature_len",
                           """在data_dir文件下，用来训练的特征文件""")
tf.app.flags.DEFINE_string("train_label_file", "train.label",
                           """在data_dir文件下，用来训练的特征文件""")
tf.app.flags.DEFINE_string("train_label_len_file", "train.label_len",
                           """在data_dir文件下，用来训练的特征文件""")

tf.app.flags.DEFINE_string("dev_feature_file", "cv.feature",
                           """在data_dir文件下，用来训练的特征文件""")
tf.app.flags.DEFINE_string("dev_feature_len_file", "cv.feature_len",
                           """在data_dir文件下，用来训练的特征文件""")
tf.app.flags.DEFINE_string("dev_label_file", "cv.label",
                           """在data_dir文件下，用来训练的特征文件""")
tf.app.flags.DEFINE_string("dev_label_len_file", "cv.label_len",
                           """在data_dir文件下，用来训练的特征文件""")

tf.app.flags.DEFINE_string("train_config_file",
                           "train.config",
                           """记录每个小文件的每行的最大的值的个数""")
tf.app.flags.DEFINE_string('dev_config_file', "cv.config",
                           """记录每个小文件的每行的最大的值的个数""")

LOGGER = logging.getLogger(__name__)


class HyperParam(yaml.YAMLObject):
  """用来表示声学模型的超参数.

  """
  yaml_tag = u'!HyperParam'


  def __init__(self, num_layers, num_hidden, init_lr, avg_decay, batch_size):
    self.num_layers = num_layers
    self.num_hidden = num_hidden
    self.init_learning_rate = init_lr
    self.moving_average_decay = avg_decay
    self.batch_size = batch_size


class BucketReader:
  """
    用来读取训练数据， 分到各个大小的桶里.

    Attributes:
      __buckets: 使用的桶数据约束列表. 每个元素由(特征约束, 标签约束)表示.
      __batch_size: 批大小, 也表示桶的大小.
      __frame_feat_num: 每一帧的特征数.
      __feature_set: 特征数据的桶.
      __feat_len_set: 特征数据长度的桶.
      __label_set: 标签数据桶.
      __feat_path: 特征数据文件路径.
      __label_path: 标签数据文件路径.
      __label_max_len: 最长的标签数量.
  """


  def __init__(self, feature_config, batch_size, feat_path, label_path):
    """

    Args:
      feature_config: 特征数据的配置信息, 是TrainDataInfo类.
      batch_size: batch大小, 也表示桶大小.
      feat_path: 特征文件的路径.
      label_path: 特征文件对应的标签文件的路径.
    """
    self.__label_max_len = feature_config.label_max_len
    self.__frame_feat_num = feature_config.feature_cols
    self.__buckets = self.__build_bucket(feature_config.frame_max_length)
    self.__batch_size = batch_size
    self.__feature_set = [[] for _ in self.__buckets]
    self.__feat_len_set = [[] for _ in self.__buckets]
    self.__label_set = [None for _ in self.__buckets]
    self.__feat_path = feat_path
    self.__label_path = label_path


  def __build_bucket(self, frame_max_len):
    """构建桶约束.

    Args:
      frame_max_len: 帧数量的上限.

    Returns:桶约束.

    """
    buckets = []
    start_frame_size = 200
    frame_num_limit = start_frame_size

    while frame_num_limit < frame_max_len:
      feature_num_limit = frame_num_limit * self.__frame_feat_num
      buckets.append((feature_num_limit, self.__label_max_len))
      frame_num_limit += 100

    max_feature_num = frame_max_len * self.__frame_feat_num
    buckets.append((max_feature_num, self.__label_max_len))
    return buckets


  def __add_to_bucket(self, features, labels):
    """把特征和标签加入到对应的桶中, 并返回桶的id.

    Args:
      features: 特征.
      labels: 特征对应的标签.

    Returns:
      桶的id

    """
    for bucket_id, (feature_size, label_size) in enumerate(self.__buckets):
      feats_len = len(features)

      if feats_len <= feature_size and len(labels) <= label_size:
        padding_features = features + [0] * (feature_size - len(features))
        self.__feature_set[bucket_id].append(padding_features)

        if self.__label_set[bucket_id] is None:
          indices = list()
          values = list()
          shape = [self.__batch_size, self.__label_max_len]

          for i in range(len(labels)):
            indices.append((0, i))
            values.append(labels[i])

          self.__label_set[bucket_id] = (indices, values, shape)
        else:
          indices = self.__label_set[bucket_id][0]
          values = self.__label_set[bucket_id][1]
          batch_index = indices[-1][0] + 1

          for i in range(len(labels)):
            indices.append((batch_index, i))
            values.append(labels[i])

        self.__feat_len_set[bucket_id].append(feats_len / self.__frame_feat_num)
        return bucket_id
    return -1

  def read_data(self):
    """获取一个batch的数据.

    Returns:
      二元组(一个batch_size大小的数据包, 以及对应bucket的id)
      数据包是一个三元组(特征数据, 特征数据对应的特征长度, 标签数据).
      其中标签数据是一个稀疏矩阵三元组(indices, values, shape).

    """
    while True:
      with open(self.__feat_path, encoding="utf-8") as feat_file, \
          open(self.__label_path, encoding="utf-8") as label_file:
        for feature_line, label_line in zip(feat_file, label_file):
          #features = [float(feat) for feat in feature_line.strip().split(",")]
          features = [float(feat) for feat in re.split("[ ,]",feature_line.strip())]
          labels = [int(label) for label in label_line.strip().split()]
          bucket_id = self.__add_to_bucket(features, labels)
          if bucket_id == -1:
            continue
          if len(self.__feature_set[bucket_id]) == self.__batch_size:
            features = self.__feature_set[bucket_id]
            features_len = self.__feat_len_set[bucket_id]
            labels = map(lambda e: np.array(e), self.__label_set[bucket_id])
            self.__feature_set[bucket_id] = list()
            self.__feat_len_set[bucket_id] = list()
            self.__label_set[bucket_id] = None
            yield (features, features_len, labels), bucket_id


class TrainDataInfo:
  """存放训练数据的一些信息，比如一个样本的长度, 一共有多少个样本等信息.

  Attributes:
    label_max_len: 一个样本的label部分的固定占用最大float32的长度.
    frame_max_length: 一个样本的特征部分的最大的帧数.
    example_number: 样本数.
    label_count: 标签种类数.
    feature_cols: 每帧特征向量的维度.
  """


  def __init__(self, frame_max_len, label_max_len,
               example_num, label_num, feat_dim):
    self.label_max_len = label_max_len
    self.frame_max_length = frame_max_len
    self.example_number = example_num
    self.label_count = label_num
    self.feature_cols = feat_dim


def read_data_config(config_path):
  """读取数据配置文件.

  Args:
    config_path: 配置文件路径.

  Returns:
    一个TrainDataInfo类.

  """
  with open(config_path) as config_file:
    config = [int(line.strip()) for line in config_file]

  return TrainDataInfo(*config)


def inference(num_hidden, num_layers, num_classes, feature_data, seq_len,
              batch_size, lstm_dropout_keep_prob=1):
  """双向LSTM网络结构，计算向前结果.

  Args:
    num_hidden: 每层宽度.
    num_layers: 层数.
    num_classes: 分类的数量.
    feature_data: 特征数据, 用于训练. 规模为[batch_size, seq_length, layer_width]
    seq_len: 序列长度.
    batch_size: batch size.

  Returns:
    在目标函数之前的模型流程.

  """
  with tf.device('/cpu:0'):
    cell_fw = tf.contrib.rnn.LSTMCell(num_hidden, use_peepholes=True,
                                      initializer=tf.random_normal_initializer(
                                        mean=0.0, stddev=0.1),
                                      state_is_tuple=True)
    if lstm_dropout_keep_prob < 1.0:
      cell_fw = tf.contrib.rnn.DropoutWrapper(cell_fw,
                                    output_keep_prob=lstm_dropout_keep_prob)

    cells_fw = [cell_fw] * num_layers
    cell_bw = tf.contrib.rnn.LSTMCell(num_hidden, use_peepholes=True,
                                      initializer=tf.random_normal_initializer(
                                        mean=0.0, stddev=0.1),
                                      state_is_tuple=True)
    if lstm_dropout_keep_prob < 1.0:
      cell_bw = tf.contrib.rnn.DropoutWrapper(cell_bw,
                                    output_keep_prob=lstm_dropout_keep_prob)

    cells_bw = [cell_bw] * num_layers

    w = tf.get_variable("weights", [num_hidden * 2, num_classes],
                        initializer=tf.random_normal_initializer(mean=0.0,
                                                                 stddev=0.1))
    b = tf.get_variable("biases", [num_classes],
                        initializer=tf.constant_initializer(0.0))

  outputs, _, _ = tf.contrib.rnn.stack_bidirectional_dynamic_rnn(cells_fw,
                                                                 cells_bw,
                                                                 feature_data,
                                                               dtype=tf.float32,
                                                        sequence_length=seq_len)

  # 做一个全连接映射到label_num个数的输出
  outputs = tf.reshape(outputs, [-1, num_hidden * 2])
  logits = tf.add(tf.matmul(outputs, w), b, name="logits_add")
  logits = tf.reshape(logits, [batch_size, -1, num_classes])
  ctc_input = tf.transpose(logits, (1, 0, 2))
  return ctc_input

def rnn(data_config, batch_size, feature_area, seq_len, hyper_params,
                                              lstm_dropout_keep_prob=1):
  """构建训练模型的RNN网络.

  Args:
    data_config: 数据相关配置.
    batch_size:
    feature_area:
    seq_len: 批特征数据每个样本对应的特征长度.
    hyper_parameters: 模型超参数.

  Returns:
    ctc_input: ctc的输入数据.

  """
  num_layers = hyper_params.num_layers
  num_hidden = hyper_params.num_hidden
  feature_cols = data_config.feature_cols
  num_classes = data_config.label_count + 1  # label的个数+1
  feature_area = tf.reshape(feature_area, [batch_size, -1, feature_cols])

  return inference(num_hidden, num_layers, num_classes, feature_area, seq_len,
              batch_size, lstm_dropout_keep_prob)


def loss_multi(logits, targets, seq_len):
  loss = tf.nn.ctc_loss(logits, targets, seq_len)
  cost = tf.reduce_mean(loss)
  tf.add_to_collection('losses', cost)
  return tf.add_n(tf.get_collection('losses'), name='total_loss')
