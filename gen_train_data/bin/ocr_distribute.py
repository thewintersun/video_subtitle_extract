# coding=utf-8
# 分布式的方式训练语音识别的声学模型
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import logging
import os
from os import path
import yaml

import tensorflow as tf

import ocr_utils

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_float('gpu_memory_fraction', 0.45, 'gpu占用内存比例')
tf.app.flags.DEFINE_string('model_dir', "../data/model_distribute/",
                           '保存模型数据的文件夹')
tf.app.flags.DEFINE_string('cuda_visible_devices', "0", '使用第几个GPU')

tf.app.flags.DEFINE_string("opt", "adam", "优化函数sgd,or adam")
# For distributed
tf.app.flags.DEFINE_string("ps_hosts", "",
                           "Comma-separated list of hostname:port pairs")
tf.app.flags.DEFINE_string("worker_hosts", "",
                           "Comma-separated list of hostname:port pairs")
tf.app.flags.DEFINE_string("job_name", "", "One of 'ps', 'worker'")
tf.app.flags.DEFINE_integer("task_index", 0, "Index of task within the job")
tf.app.flags.DEFINE_integer("issync", 0, "是否采用分布式的同步模式，1表示同步模式，0表示异步模式")


def train():

  ps_hosts = FLAGS.ps_hosts.split(",")
  worker_hosts = FLAGS.worker_hosts.split(",")
  cluster = tf.train.ClusterSpec({"ps": ps_hosts, "worker": worker_hosts})

  gpu_options = tf.GPUOptions(
    per_process_gpu_memory_fraction=FLAGS.gpu_memory_fraction)

  server = tf.train.Server(cluster,
                           config=tf.ConfigProto(gpu_options=gpu_options),
                           job_name=FLAGS.job_name,
                           task_index=FLAGS.task_index)

  issync = FLAGS.issync

  if FLAGS.job_name == "ps":
    server.join()
  elif FLAGS.job_name == "worker":
    batch_size = FLAGS.batch_size

    train_filename = os.path.join(FLAGS.data_dir, FLAGS.train_file)
    cv_filename = os.path.join(FLAGS.data_dir, FLAGS.cv_file)
	
    with tf.device('/cpu:0'):
      images, labels = ocr_utils.inputs(train_filename, batch_size=batch_size)
      cv_images, cv_labels = ocr_utils.inputs(cv_filename, batch_size=batch_size)
    
    dev_examples_num = 16130
    train_num_examples = 10992522
	
    dev_num_batches_per_epoch = int(dev_examples_num/ batch_size)
    train_num_batches_per_epoch = int(train_num_examples/ batch_size)

    initial_learning_rate = FLAGS.initial_learning_rate

    with tf.device(tf.train.replica_device_setter(
        worker_device="/job:worker/task:%d" % FLAGS.task_index,
        cluster=cluster)):
      global_step = tf.get_variable('global_step', [],
                                    initializer=tf.constant_initializer(0),
                                    trainable=False, dtype=tf.int32)

      if FLAGS.opt == "sgd":
        optimizer = tf.train.GradientDescentOptimizer(initial_learning_rate)
      if FLAGS.opt == "adam":
        optimizer = tf.train.AdamOptimizer(initial_learning_rate)

      seq_len = [730] * batch_size

      with tf.variable_scope("inference") as scope:
        train_ctc_in = ocr_utils.inference(images, seq_len, batch_size)
        scope.reuse_variables()
        dev_ctc_in = ocr_utils.inference(cv_images, seq_len, batch_size)

      train_ctc_losses = tf.nn.ctc_loss( labels, train_ctc_in,
                                        seq_len)
      train_cost = tf.reduce_mean(train_ctc_losses, name="train_cost")
      # 限制梯度范围
      grads_and_vars = optimizer.compute_gradients(train_cost)
      capped_grads_and_vars = grads_and_vars
      capped_grads_and_vars = [(tf.clip_by_value(gv[0], -50.0, 50.0), gv[1]) for gv in grads_and_vars]

      if issync == 1:
        #同步模式计算更新梯度
        rep_op = tf.train.SyncReplicasOptimizer(optimizer,
                                                replicas_to_aggregate=len(
                                                  worker_hosts),
                                                replica_id=FLAGS.task_index,
                                                total_num_replicas=len(
                                                  worker_hosts),
                                                use_locking=True)
        train_op = rep_op.apply_gradients(capped_grads_and_vars,
                                       global_step=global_step)
        merge_train_ops = [train_op] 
        init_token_op = rep_op.get_init_tokens_op()
        chief_queue_runner = rep_op.get_chief_queue_runner()
      else:
        #异步模式计算更新梯度
        train_op = optimizer.apply_gradients(capped_grads_and_vars,
                                       global_step=global_step)
        merge_train_ops = [train_op] 

      #记录loss值，显示到tensorboard上
      #tf.scalar_summary("train_cost", train_cost)

      #dev 评估
      dev_decoded, dev_log_prob = tf.nn.ctc_greedy_decoder(dev_ctc_in, seq_len)
      dev_edit_distance = tf.edit_distance(tf.to_int32(dev_decoded[0]), cv_labels,
                                   normalize=False)
      dev_batch_error_count = tf.reduce_sum(dev_edit_distance)
      dev_batch_label_count = tf.shape(cv_labels.values)[0]
  
      # train 评估
      train_decoded, train_log_prob = tf.nn.ctc_greedy_decoder(train_ctc_in, seq_len)
      train_edit_distance = tf.edit_distance(tf.to_int32(train_decoded[0]), labels,
                                   normalize=False)
      train_batch_error_count = tf.reduce_sum(train_edit_distance)
      train_batch_label_count = tf.shape(labels.values)[0]

      # 初始化各种
      init_op = tf.global_variables_initializer()
      local_init = tf.local_variables_initializer()
      saver = tf.train.Saver()
      summary_op = tf.summary.merge_all()

      sv = tf.train.Supervisor(is_chief=(FLAGS.task_index == 0),
                               logdir=FLAGS.model_dir,
                               init_op=init_op,
                               local_init_op=local_init,
                               summary_op=summary_op,
                               saver=saver,
                               global_step=global_step,
                               save_model_secs=3600)

      with sv.prepare_or_wait_for_session(server.target) as sess:
        # 如果是同步模式
        if FLAGS.task_index == 0 and issync == 1:
          sv.start_queue_runners(sess, [chief_queue_runner])
          sess.run(init_token_op)

        summary_writer = tf.summary.FileWriter(FLAGS.model_dir, sess.graph)

        step = 0
        valid_step = 0
        train_acc_step = 0
        epoch = 0
        while not sv.should_stop() and step < 100000000:
          
          _,loss, step = sess.run([merge_train_ops,train_cost,global_step])

          if (step - train_acc_step) > 1000:
            train_acc_step = step
            
            train_error_count_value, train_label_count = sess.run(
              [train_batch_error_count, train_batch_label_count])
            train_acc_ratio = (train_label_count - train_error_count_value) / train_label_count
            logging.info("eval: step = %d loss = %.3f train_acc = %.3f ", step, loss,
						                 train_acc_ratio)

		      # 当跑了steps_to_validate个step，并且是主的worker节点的时候， 评估下数据
		      # 因为是分布式的，各个节点分配了不同的step，所以不能用 % 是否等于0的方法
          if step - valid_step > int(train_num_batches_per_epoch/4) and FLAGS.task_index == 0:
            epoch += 1
            valid_step = step
            dev_error_count = 0
            dev_label_count = 0

            for batch in range(dev_num_batches_per_epoch):

              dev_error_count_value, dev_label_count_value = sess.run(
                [dev_batch_error_count, dev_batch_label_count])
              dev_error_count += dev_error_count_value
              dev_label_count += dev_label_count_value

            dev_acc_ratio = (dev_label_count - dev_error_count) / dev_label_count
            logging.info("epoch: %d eval: step = %d eval_acc = %.3f ",
						 epoch,
						 step, dev_acc_ratio)

if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                      datefmt='%a, %d %b %Y %H:%M:%S',
                      filename='./out.log',
                      filemode='a')
  os.environ["CUDA_VISIBLE_DEVICES"] = FLAGS.cuda_visible_devices

  train()
