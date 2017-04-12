#coding=utf-8
import wave
import numpy as np
import python_speech_features as psf
import asrmodel
import os
import codecs
import MySQLdb
import traceback
from pydub import AudioSegment
import pinyin
import shutil
import time
import commands
import threading
import time
import argparse
import multiprocessing

def is_ustr(in_str):
    out_str=''
    for i in range(len(in_str)):
        if is_uchar(in_str[i]):
            out_str=out_str+in_str[i]
        else:
            out_str=out_str+' '
    return out_str
def is_uchar(uchar):

    """判断一个unicode是否是汉字"""
    if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
            return True
    """判断一个unicode是否是数字"""
    if uchar >= u'\u0030' and uchar<=u'\u0039':
            return True
    """判断一个unicode是否是英文字母"""
    if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
            return True
    #if uchar in ('-',',','，','。','.','>','?'):
    #        return True
    return False

def read_config():
  myip="127.0.0.1"
  config_file= "../download/config/config"
  with codecs.open(config_file, 'r', 'utf-8') as fr:
    for line in fr:
      if line.startswith("#"):
        continue
      w1,w2 = line.strip().split('    ')
      if w1 == "localip":
        myip = w2
  return myip
  
def extract_feature(sig, rate, feature_type="MFCC", cmvn=True, delta=True):
  """ 从音频文件中抽取特征.

  Returns:
    特征向量, 规模是[帧数, 特征向量维度]

  """
  if feature_type == "fbank":
    feature = psf.logfbank(sig, rate)
  elif feature_type == "MFCC":
    feature = psf.mfcc(sig, rate)
  else:
    raise ValueError("不支持的特征抽取方法.")
  if cmvn:
    cmvn_stats = np.zeros((2, feature.shape[1] + 1))
    cmvn_stats[0, :-1] = feature.sum(axis=0)
    cmvn_stats[0, -1] = feature.shape[0]
    cmvn_stats[1, :-1] = (feature ** 2).sum(axis=0)
    norm_stats = np.zeros((2, feature.shape[1]))
    mean = cmvn_stats[0, :-1] / cmvn_stats[0, -1]
    var = cmvn_stats[1, :-1] / cmvn_stats[0, -1] - mean * mean
    var = np.maximum(var, 1e-20)
    scale = 1 / np.sqrt(var)
    norm_stats[0] = -(mean * scale)
    norm_stats[1] = scale
    feature = np.dot(feature, np.diag(norm_stats[1]))
    feature += norm_stats[0]

  if delta:
    delta_feat = psf.delta(feature, 2)
    delta_delta_feat = psf.delta(delta_feat, 2)
    feature = np.column_stack((feature, delta_feat, delta_delta_feat))

  return feature

def pad_features(feature, row_number):
  if feature.shape[0] < row_number:
    add_feature = np.zeros((row_number - len(feature), feature.shape[1]))
    return np.concatenate((feature, add_feature))
  print("feature length is longer than %d, real is %d" %(row_number, feature.shape[0]))
  return feature[:row_number,]
  
def cut_wav_and_match(phn_model,phn_model2, wav_save_path,temp_export_wav_dir, start_time, end_time, subtitle, phn_dict):
  wav_audio = AudioSegment.from_wav(wav_save_path)
  max_start_before_step = 3
  max_start_after_step = 2
  max_end_before_step = 3
  max_end_after_step = 3
  step_time = 200
  in_step_time = step_time

  start_time = int(float(start_time) * 1000)
  end_time = int(float(end_time) * 1000)
  
  if end_time - (max_end_before_step * step_time) - (start_time + (max_start_after_step+1)*step_time) < 0:
    in_step_time = int(float(end_time - start_time) /(2*(max_start_after_step + max_end_before_step)))

  export_filename_list = []
  test_start_time_list = []
  test_end_time_list = []
  seq_len_list = []
  feature_list = []
  for before_step in range(-max_start_before_step, max_start_after_step):
    for after_step in range(-max_end_before_step, max_end_after_step):
      before_real_step_time  = step_time
      after_real_step_time  = step_time
      if before_step > 0:
        before_real_step_time = in_step_time
      if after_step < 0:
        after_real_step_time = in_step_time

      test_start_time = int(start_time + before_step * before_real_step_time)
      test_end_time = int(end_time + after_step * after_real_step_time)

      test_start_time = max(0, test_start_time)
      if test_start_time >= test_end_time:
        print("subtitle's wav file is too short %s %f %f" %(subtitle, start_time, end_time))
        return

      export_filename = os.path.join(temp_export_wav_dir,str(test_start_time)  + str(test_end_time) + ".wav")
      wav_audio[test_start_time:test_end_time].export(export_filename, format="wav")
      
      export_filename_list.append(export_filename)
      test_start_time_list.append(test_start_time)
      test_end_time_list.append(test_end_time)


      wave_file = wave.open(export_filename, "rb")
      params = wave_file.getparams()
      nchannels, sampwidth, framerate, nframes = params[:4]
      str_data = wave_file.readframes(nframes)
      wave_file.close()
      wave_data = np.fromstring(str_data, dtype=np.short)
      if nchannels == 2:
        wave_data.shape = -1, 2
        wave_data = wave_data[:,1]
        mfcc_feature = extract_feature(wave_data, framerate)
      seq_len_list.append(mfcc_feature.shape[0])
      mfcc_feature = pad_features(mfcc_feature, 600)
      
      feature_list.append(mfcc_feature)
      #phn_model.feature_to_greedy_ctc_decode([mfcc_feature], [mfcc_feature.shape[0]])

  ctc_decode_units = phn_model.feature_to_greedy_ctc_decode(feature_list, seq_len_list)
  ctc_decode_units2 = phn_model2.feature_to_greedy_ctc_decode(feature_list, seq_len_list)

  try:
    subtitle_first_phn1 = phn_dict[subtitle[0]][0]
    subtitle_first_phn2 = phn_dict[subtitle[0]][1]
    subtitle_last_phn1 = phn_dict[subtitle[-1]][0]
    subtitle_last_phn2 = phn_dict[subtitle[-1]][1]
  except:
    traceback.print_exc()
    print("except subtitle is %s" % subtitle)
    return "",""


  #print(subtitle_first_phn1,subtitle_first_phn2,subtitle_last_phn1,subtitle_last_phn2)
  #print(ctc_decode_units)

  final_export_filename = ""
  final_test_start_time = 0
  final_test_end_time   = 7200000

  for i in range(len(ctc_decode_units)):
    ctc_decode_phn = ctc_decode_units[i]
    ctc_decode_phn2 = ctc_decode_units2[i]
    export_filename = export_filename_list[i]
    test_start_time = test_start_time_list[i]
    test_end_time = test_end_time_list[i]
    
    if len(ctc_decode_phn) < 2 or len(ctc_decode_phn2) < 2:
      continue
    if (ctc_decode_phn[0] == subtitle_first_phn1 and ctc_decode_phn[1] == subtitle_first_phn2 \
        and ctc_decode_phn[-2] == subtitle_last_phn1 and ctc_decode_phn[-1] == subtitle_last_phn2) or \
       (ctc_decode_phn2[0] == subtitle_first_phn1 and ctc_decode_phn2[1] == subtitle_first_phn2 \
        and ctc_decode_phn2[-2] == subtitle_last_phn1 and ctc_decode_phn2[-1] == subtitle_last_phn2):
      
      if test_start_time > final_test_start_time or test_end_time < final_test_end_time:
        final_test_start_time = test_start_time
        final_test_end_time = test_end_time
        final_export_filename = export_filename

  return final_export_filename, float(final_test_end_time - final_test_start_time)/ 1000 


	  
def reconnect_mysql():
  conn= MySQLdb.connect(
        host='192.168.100.71',
        port = 3306,
        user='root',
        passwd='luodongri',
        db ='video',
        charset="utf8",)
  cur = conn.cursor()
  return conn,cur

def set_process_flag(cur, conn, id):
  sqli="update wav_and_text set is_processed=1 where Id="+str(id)
  ret = cur.execute(sqli)
  conn.commit()
def set_processed_flag(cur, conn, id):
  sqli="update wav_and_text set is_processed=2 where Id="+str(id)
  ret = cur.execute(sqli)
  conn.commit()

def reset_process_flag(cur, conn, id):
  sqli="update wav_and_text set is_processed=0 where Id="+str(id)
  ret = cur.execute(sqli)
  conn.commit()
  
current_thread_number = 0
max_thread_num=2
class WorkThread(threading.Thread):
  current_thread_number = 0
  @classmethod
  def add_current_thread_number(cls):
    cls.current_thread_number += 1

  @classmethod
  def sub_current_thread_number(cls):
    cls.current_thread_number -= 1

  @classmethod
  def get_current_thread_number(cls):
    return cls.current_thread_number

  def __init__(self, lock, output_data_dir, phn_model,phn_model2, phn_dict, myip, py):
    threading.Thread.__init__(self)
    self.lock = lock
    self.output_data_dir = output_data_dir
    self.phn_model = phn_model
    self.phn_model2 = phn_model2
    self.phn_dict = phn_dict
    self.myip = myip
    self.py = py

  def run(self):
    print(time.time())
    conn, cur = reconnect_mysql()
    self.lock.acquire()
    result_number = cur.execute("select Id, wav_save_path, subtitle_file_path,wav_class from wav_and_text where is_processed=0 and wav_save_ip='"+ self.myip+"' order by Id asc limit 1")
    if result_number == 0:
      print("all wav at this machine is processed, exit this thread")
      cur.close()
      conn.close()
      WorkThread.sub_current_thread_number()
      self.lock.release()
      return
    db_result = cur.fetchone()
    id = db_result[0]
    wav_save_path = db_result[1].strip()
    subtitle_file_path = db_result[2].strip()
    wav_class = db_result[3].strip()

    subtitle_file_name = subtitle_file_path.split('/')[-1]
    subtitle_file_name_prefix = subtitle_file_name.split(".")[0]
    temp_export_wav_dir = os.path.join("./temp/", subtitle_file_name_prefix)
  
    set_process_flag(cur, conn, id)
    self.lock.release()
    cur.close()
    conn.commit()
    conn.close()

    #建立输出wav和stm的文件夹
    output_wav_class_path = os.path.join(self.output_data_dir, wav_class)
    if not os.path.exists(output_wav_class_path):
      os.makedirs(output_wav_class_path)

    output_train_dir = os.path.join(output_wav_class_path, subtitle_file_name_prefix)
    if not os.path.exists(output_train_dir):
      os.makedirs(output_train_dir)
    output_stm_dir = os.path.join(output_train_dir, "stm")
    output_wav_dir = os.path.join(output_train_dir, "wav")
    if not os.path.exists(output_stm_dir):
      os.makedirs(output_stm_dir)
    if not os.path.exists(output_wav_dir):
      os.makedirs(output_wav_dir)
    if not os.path.exists(temp_export_wav_dir):
      os.makedirs(temp_export_wav_dir)

    with codecs.open(subtitle_file_path, 'r', 'utf-8') as subtitle_reader:
      #这里做一个计数，如果这个文件一个字幕也没识别出来，可能出现了问题，就打印出来
      find_correct_subtitle_number = 0
      for line in subtitle_reader:

        line_splits = line.strip().split('\t')
        start_time = line_splits[1]
        end_time = line_splits[2]
        subtitle = line_splits[3]
        subtitle = is_ustr(subtitle)
     
        try: 
          export_filepath, duration_time = cut_wav_and_match(self.phn_model,phn_model2, wav_save_path, \
                           temp_export_wav_dir, start_time, end_time, subtitle, self.phn_dict)
        except:
          traceback.print_exc()
          print("may the wav is less than the video file %s" %wav_save_path.encode('utf-8'))
          continue

        if export_filepath == "":
          #表示没有找到
          continue
        print(subtitle)
        find_correct_subtitle_number += 1
        #找到对应字幕的文件片段，复制文件出来，
        export_file_name = export_filepath.split('/')[-1]
        export_file_name_prefix = export_file_name.split(".")[0]
        subtitle_file_name_pinyin = self.py.get_pinyin(subtitle_file_name_prefix)
        if len(subtitle_file_name_pinyin) > 6:
          subtitle_file_name_pinyin = subtitle_file_name_pinyin[:6]
        copy_dst_filename = subtitle_file_name_pinyin + str(time.strftime("%Y", time.localtime())) + export_file_name_prefix
        copy_dst_filepath = os.path.join(output_wav_dir, copy_dst_filename + ".wav")
        shutil.copyfile(export_filepath, copy_dst_filepath) 
       
        stm_file_path = os.path.join(output_stm_dir, copy_dst_filename + ".stm")
        with codecs.open(stm_file_path, 'w', 'utf-8') as stm_fw:
          stm_fw.write(copy_dst_filename+ " A " + copy_dst_filename + " 0 "+ str(duration_time) + " <o,f0,female> " + subtitle + "\n")

      if find_correct_subtitle_number <2:
        print("no subtitle find in the video: %s" % subtitle_file_path) 

    #处理时间太长mysql会自动断开
    conn, cur = reconnect_mysql()
    set_processed_flag(cur, conn, id)
    cur.close()
    conn.commit()
    conn.close()

    #删除临时文件夹
    temp_export_wav_dir
    command = "rm -rf " + temp_export_wav_dir
    command = command.encode('utf-8')
    (status, output) = commands.getstatusoutput(command)

    WorkThread.sub_current_thread_number()
    print(time.time())

def run():
  py = pinyin.Pinyin()
  #模型相关
  model_dir = "/asrDataCenter/dataCenter/modelCenter/asr/tensorflow/md_16k_797/"
  model_dir2 = "/asrDataCenter/dataCenter/modelCenter/asr/tensorflow/all_16k_886/"
  zdict_path = "/asrDataCenter/phn_dict/zdict.dict"
  
  units_file = os.path.join(model_dir, "units.txt")
  unit_dict = {}
  phn_dict = {}
  with codecs.open(units_file, 'r', 'utf-8') as unit_reader, codecs.open(zdict_path, 'r','utf-8') as zdict_reader:
    for line in unit_reader:
      phn, phn_id = line.strip().split()
      unit_dict[int(phn_id)] = phn
    for line in zdict_reader:
      line_splits = line.strip().split()
      phn_dict[line_splits[0]] = line_splits[1:]

  phn_model = asrmodel.AsrModel(model_dir,  "inference")
  phn_model2 = asrmodel.AsrModel(model_dir2, "inference_355h")

  output_data_dir = "/disk2/videowavdata"
  if not os.path.exists(output_data_dir):
    os.makedirs(output_data_dir)

  lock = threading.Lock()
  times=0
  maxtimes = 4
  while times < maxtimes:
    time.sleep(5)
    times += 1
    work_thread = WorkThread(lock, output_data_dir, phn_model,phn_model2, phn_dict, myip, py)
    work_thread.start()
    WorkThread.add_current_thread_number()
    print(WorkThread.get_current_thread_number())
    while WorkThread.get_current_thread_number() >= 2:
      time.sleep(0.1)

  work_thread.join()
  print("asr process execute over ,exit.....")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("is_use_gpu", help="是否使用gpu,1使用，0不使用", type=int)
  parser.add_argument("use_gpus", help="使用哪些gpu,格式0,1,2,3", type=str)
  args = parser.parse_args()

  is_use_gpu = args.is_use_gpu
  use_gpus   = args.use_gpus
  use_gpus_list = use_gpus.strip().split(",")
  use_gpu_number = len(use_gpus_list)

  #如果没有使用gpu，使用cpu，默认使用4个多进程
  processes_number = 4
  if is_use_gpu == 1:
    processes_number = use_gpu_number

  myip=read_config()
  pool = multiprocessing.Pool(processes = processes_number)

  
  for gpu_id in use_gpus_list:
    time.sleep(10)
    pool.apply_async(run,(is_use_gpu, gpu_id ))
  pool.close()  
  pool.join()  
  

  



