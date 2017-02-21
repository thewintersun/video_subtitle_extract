# coding=utf-8
# 定义模型结构, 数据预处理.
import sys

import tensorflow as tf
import yaml

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_integer('dev_batch_size', 10, """dev的测试的batch size""")

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
    用来读取训练数据， 分到各个大小的bucket里面
  """


  def __init__(self, buckets, feature_num_per_frame, batch_size):
    self.buckets = buckets
    self.batch_size = batch_size
    self.feature_num_per_frame = feature_num_per_frame
    self.total_read_counter = 0
    self.feature_set = [[] for _ in buckets]
    self.feature_len_set = [[] for _ in buckets]
    self.label_set = [[] for _ in buckets]
    self.label_len_set = [[] for _ in buckets]


  def read_data(self, feature_file, feature_len_file, label_file,
                label_len_file):
    feature_line, feature_len_line, label_line, label_len_line = \
      feature_file.readline(), feature_len_file.readline(), \
      label_file.readline(), label_len_file.readline()

    if not feature_line or not feature_len_line or not label_line or not label_len_line:
      feature_file.seek(0, 0)
      feature_len_file.seek(0, 0)
      label_file.seek(0, 0)
      label_len_file.seek(0, 0)

      feature_line, feature_len_line, label_line, label_len_line = \
        feature_file.readline(), feature_len_file.readline(), \
        label_file.readline(), label_len_file.readline()

    while feature_line and feature_len_line and label_line and label_len_line:
      self.total_read_counter += 1

      if self.total_read_counter % 1000 == 0:
        print("  reading data line %d" % self.total_read_counter)
        sys.stdout.flush()

      feature_ids = [float(x) for x in feature_line.split()]
      seq_len_ids = [int(int(x) / self.feature_num_per_frame) for x in
                     feature_len_line.split()]
      label_ids = [int(x) for x in label_line.split()]
      label_len_ids = [int(x) for x in label_len_line.split()]

      for bucket_id, (frame_size, label_size) in enumerate(self.buckets):
        if len(feature_ids) < frame_size * self.feature_num_per_frame and len(
            label_ids) < label_size:
          temp_feature_ids = feature_ids + [0] * (
            frame_size * self.feature_num_per_frame - len(feature_ids))
          temp_label_ids = label_ids + [0] * (label_size - len(label_ids))
          self.feature_set[bucket_id].append(temp_feature_ids)
          self.feature_len_set[bucket_id].extend(seq_len_ids)
          self.label_set[bucket_id].append(temp_label_ids)
          self.label_len_set[bucket_id].extend(label_len_ids)
          break

      if len(self.feature_set[bucket_id]) == self.batch_size:
        patch_data = [self.feature_set[bucket_id],
                      self.feature_len_set[bucket_id],
                      self.label_set[bucket_id],
                      self.label_len_set[bucket_id]]
        self.feature_set[bucket_id] = []
        self.feature_len_set[bucket_id] = []
        self.label_set[bucket_id] = []
        self.label_len_set[bucket_id] = []
        return patch_data, bucket_id

      feature_line, feature_len_line, label_line, label_len_line = \
        feature_file.readline(), feature_len_file.readline(), \
        label_file.readline(), label_len_file.readline()

      # 如果文件读完了， seek到最开头
      if not feature_line or not feature_len_line or not label_line or not label_len_line:
        feature_file.seek(0, 0)
        feature_len_file.seek(0, 0)
        label_file.seek(0, 0)
        label_len_file.seek(0, 0)

        feature_line, feature_len_line, label_line, label_len_line = \
          feature_file.readline(), feature_len_file.readline(), \
          label_file.readline(), label_len_file.readline()


class TrainDataInfo:
  """存放训练数据的一些信息，比如一个样本的长度
  一共有多少个样本等信息
  """


  def __init__(self):
    self.label_max_length = 0  # 一个样本的label部分的固定占用最大float32的长度
    self.frame_max_length = 0  # 一个样本的特征部分的最大的帧数
    self.example_number = 0  # 一共有多少个样本
    self.example_label_count = 0  # 所有的label的个数， 一般是70-90左右
    self.feature_cols = 0  # 一帧包含多少个特征值


def read_data_config(config_path):
  """读取数据配置文件.

  Args:
    config_path: 配置文件路径.

  Returns:
    (一个样本最大的占多少个float32,
    特征部分占多少个float32的个数,
    label最大占多少个float32的个数,
    样本的个数,
    label的类型的个数,
    一帧数据的特征数个数)

  """
  config = list()

  with open(config_path) as config_file:
    for line in config_file:
      config.append(int(line.strip()))

  train_data_info = TrainDataInfo()
  train_data_info.frame_max_length = int(config[0])
  train_data_info.label_max_length = int(config[1])
  train_data_info.example_number = int(config[2])
  train_data_info.example_label_count = int(config[3])
  train_data_info.feature_cols = int(config[4])
  return train_data_info

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
    cell_fw = tf.contrib.rnn.LSTMCell(num_hidden, 
                                      initializer=tf.random_normal_initializer(
                                        mean=0.0, stddev=0.1),
                                      state_is_tuple=True)
    if lstm_dropout_keep_prob < 1.0:
      cell_fw = tf.contrib.rnn.DropoutWrapper(cell_fw,
                                    output_keep_prob=lstm_dropout_keep_prob)

    cells_fw = [cell_fw] * num_layers
    cell_bw = tf.contrib.rnn.LSTMCell(num_hidden,
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


def rnn(data_config, batch_size, feature_area, seq_len,
        label_area, label_len, hyper_parameters):
  """构建训练模型的RNN网络.

  Args:
    inputs: 特征数据, 第一维是batch size, 后面记录了各种标签数据.
    data_config: 数据相关配置.

  Returns:
    返回三元组, 分别是
    ctc_input: ctc的输入数据.
    targets: 训练数据的正确标签, 以稀疏矩阵的形式表示.
    seq_len:  每个batch的长度.

  """
  num_layers = hyper_parameters.num_layers
  num_hidden = hyper_parameters.num_hidden
  feature_cols = data_config.feature_cols
  num_classes = data_config.example_label_count + 1  # label的个数+1

  # 处理输入的数据，提取特征数据
  feature_area = tf.reshape(feature_area, [batch_size, -1, feature_cols],
                            name="feature_area")

  ctc_input = inference(num_hidden, num_layers, num_classes,
                        feature_area,
                        seq_len,
                        batch_size)

  # label的所有值，将label的数据转换成SparseTensor的形式
  # TODO: 可以简化, 用batch中的样例id pack label本身即可.
  label_value = tf.slice(label_area, [0, 0], [1, label_len[0]])

  for i in range(1, batch_size):
    v1 = tf.slice(label_area, [i, 0], [1, label_len[i]])
    label_value = tf.concat(1, [label_value, v1])

  label_value = tf.reshape(label_value, [-1])
  indices = tf.range(data_config.label_max_length)

  indice1 = tf.fill([label_len[0]], 0)
  indice2 = tf.slice(indices, [0], [label_len[0]])
  indices_array = tf.pack([indice1, indice2], axis=1)

  for i in range(1, batch_size):
    indice1 = tf.fill([label_len[i]], i)
    indice2 = tf.slice(indices, [0], [label_len[i]])
    temp_array = tf.pack([indice1, indice2], axis=1)
    indices_array = tf.concat(0, [indices_array, temp_array])

  sparse_shape = [batch_size, data_config.label_max_length]
  sparse_shape = tf.to_int64(sparse_shape)
  indices_array = tf.to_int64(indices_array)
  label_value = tf.to_int32(label_value)
  targets = tf.SparseTensor(indices_array, label_value, sparse_shape)
  return ctc_input, targets, seq_len


def loss_multi(logits, targets, seq_len):
  loss = tf.nn.ctc_loss(logits, targets, seq_len)
  cost = tf.reduce_mean(loss)
  tf.add_to_collection('losses', cost)
  return tf.add_n(tf.get_collection('losses'), name='total_loss')
