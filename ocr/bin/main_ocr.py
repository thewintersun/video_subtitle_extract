#coding=utf-8
import commands
import os
import ocr_and_find_txt
import ocrmodel
import codecs
import MySQLdb
import traceback
import merge_ocr_subtitle
import threading
import time
import shutil
import argparse
import multiprocessing



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
  sqli="update iqiyi_list set process_flag=1 where Id="+str(id)
  ret = cur.execute(sqli)
  conn.commit()

def set_processed_flag(cur, conn, id):
  sqli="update iqiyi_list set process_flag=2 where Id="+str(id)
  ret = cur.execute(sqli)
  conn.commit()

def reset_process_flag(cur, conn, id):
  sqli="update iqiyi_list set process_flag=0 where Id="+str(id)
  ret = cur.execute(sqli)
  conn.commit()
def set_process_flag_except(cur, conn, id):
  sqli="update iqiyi_list set process_flag=3 where Id="+str(id)
  ret = cur.execute(sqli)
  conn.commit()
def set_process_flag_pass(cur, conn, id):
  sqli="update iqiyi_list set process_flag=4 where Id="+str(id)
  ret = cur.execute(sqli)
  conn.commit()

def read_config():
  myip="127.0.0.1"
  config_file= "../../download/config/config"
  with codecs.open(config_file, 'r', 'utf-8') as fr:
    for line in fr:
      if line.startswith("#"):
        continue
      w1,w2 = line.strip().split('    ')
      if w1 == "localip":
        myip = w2
  return myip




class WorkThread(threading.Thread):
  current_thread_number = 0
  def __init__(self, lock, gpu_id, cut_video_dir, tf_model, wav_dir, ocr_merge_record_dir, ocr_record_dir, snapshot_record_dir):
    threading.Thread.__init__(self)
    self.lock = lock
    self.gpu_id = gpu_id
    self.cut_video_dir = cut_video_dir
    self.tf_model = tf_model
    self.wav_dir = wav_dir
    self.ocr_merge_record_dir = ocr_merge_record_dir
    self.ocr_record_dir = ocr_record_dir
    self.snapshot_record_dir = snapshot_record_dir

  @classmethod
  def add_current_thread_number(cls):
    cls.current_thread_number += 1

  @classmethod
  def sub_current_thread_number(cls):
    cls.current_thread_number -= 1

  @classmethod
  def get_current_thread_number(cls):
    return cls.current_thread_number

  def run(self):
    conn, cur = reconnect_mysql()
	
    self.lock.acquire()
    result_number = cur.execute("select Id, video_class, save_path from iqiyi_list where video_class in (select video_class from subtitle_pos) and is_download=1 and process_flag=0 and save_ip='"+myip+"' order by Id asc limit 1")
    if result_number == 0:
      print("[%s] all video at this machine is processed, exit this thread" % (self.gpu_id))
      cur.close()
      conn.close()
      WorkThread.sub_current_thread_number()

      self.lock.release()
      return
  
    db_result = cur.fetchone()
    id = db_result[0]
    video_class = db_result[1].strip()
    save_path = db_result[2].strip()
    save_file_name = save_path.split('/')[-1]
    file_name_prefix = save_file_name.split(".")[0]
    print("[%s] process: %d %s %s" %(self.gpu_id, id, video_class, save_path))
  
    set_process_flag(cur, conn, id)
    self.lock.release()

    #获取坐标
    sql = "select margin_top, margin_left, height,mintime from subtitle_pos where video_class='"  + video_class+ "'"

    try:
      ret = cur.execute(sql)
    except:
      traceback.print_exc()
      set_process_flag_except(cur, conn, id)
      print("[%s] not video_class find in database, video_class is %s" % (self.gpu_id, video_class))
      WorkThread.sub_current_thread_number()
      return
    if ret == 0:
      print("[%s] not video_class find in database, video_class is %s" % (self.gpu_id, video_class))
      set_process_flag_except(cur, conn, id)
      cur.close()
      conn.close()
      WorkThread.sub_current_thread_number()
      return

    db_result = cur.fetchone()
    top = db_result[0]
    left= db_result[1]
    height = db_result[2]
    mintime= db_result[3]

    if top==None or left == None or height == None:
      print("[%s] not video_class left height top info find in database, video_class is %s" % (self.gpu_id, video_class))
      set_process_flag_except(cur, conn, id)
      cur.close()
      conn.close()
      WorkThread.sub_current_thread_number()
      return

    #判断视频的时长是否太短
    command = "./is_video_too_short.sh " + save_path + " " + str(mintime)
    print(command)
    command = command.encode('utf-8')
    (status, output) = commands.getstatusoutput(command)
    if status != 0:
      print("[%s] this video time is shorter than %d s, pass it! %s" % (self.gpu_id, mintime,save_path))
      set_process_flag_pass(cur, conn, id)
      cur.close()
      conn.commit()
      conn.close()
      WorkThread.sub_current_thread_number()
      return

    #进行视频切割
    cut_file_path =  os.path.join(self.cut_video_dir, save_file_name)
    temp_cut_file_path =  os.path.join(self.cut_video_dir, "temp_" + save_file_name)
    print("[%s] start cut the video %s"% (self.gpu_id, cut_file_path))
    #先去掉音频，处理会快一些
    command = "ffmpeg -y -i " + save_path + " -vcodec copy -an " +  temp_cut_file_path
    print(command)
    command = command.encode('utf-8')
    (status, output) = commands.getstatusoutput(command)

    #再切视频
    command = "./cut_video.sh " + temp_cut_file_path + " 730 " + str(height) + " " + str(left) + " " + str(top) + " " +  cut_file_path
    print(command)
    command = command.encode('utf-8')
    (status, output) = commands.getstatusoutput(command)
    if status != 0:
      #cut出错
      print("[%s] cut video error: %d" % (self.gpu_id, status))
      reset_process_flag(cur, conn, id)
      WorkThread.sub_current_thread_number()
      return
  
    #删除temp视频
    if os.path.exists(temp_cut_file_path):
      os.remove(temp_cut_file_path)
    print("end cut the video %s"% cut_file_path)



    #对切割的视频，进行截图
    print("[%s] start snapshot the video %s" % (self.gpu_id, cut_file_path))
    time_pic_record_file = self.snapshot_record_dir + "/" + file_name_prefix + ".record"
    command = "./snapshot_all.sh " +  cut_file_path+ " ../snapshot_dir/"+ file_name_prefix + " " +   file_name_prefix + " " + time_pic_record_file
    print(command)
    command = command.encode('utf-8')
    (status, output) = commands.getstatusoutput(command)

    print("[%s] end snapshot, return is %d %s" % (self.gpu_id, status, cut_file_path))
    
    # 因为后面的处理时间很长，mysql的链接会被服务器断掉，这里先关闭，后面再开启
    cur.close()
    conn.commit()
    conn.close()

    #进行ocr识别
    print("[%s] start ocr the snapshoted pic %s" % (self.gpu_id, time_pic_record_file))
    snapshot_record_file= time_pic_record_file
    ocr_record_file=os.path.join(self.ocr_record_dir, file_name_prefix+".record")
    ocr_and_find_txt.ocr(self.tf_model, snapshot_record_file, ocr_record_file)
    print("[%s] end ocr the snapshoted pic, record result in %s" % (self.gpu_id, ocr_record_file))


    #merge ocr识别的结果
    print("[%s] start merge ocr result %s" % (self.gpu_id, ocr_record_file))
    ocr_merge_record_file = os.path.join(self.ocr_merge_record_dir, file_name_prefix+".record")
    merge_ocr_subtitle.merge_record(ocr_record_file, ocr_merge_record_file)
    print("[%s] end merge ocr result" %(self.gpu_id))

  
    #转wav
    wav_file=os.path.join(self.wav_dir, file_name_prefix+".wav")
    print("[%s] start convert video to wav %s" % (self.gpu_id, wav_file))
    command = "./video2wav.sh " + save_path + " " + wav_file
    print(command)
    command = command.encode('utf-8')
    (status, output) = commands.getstatusoutput(command)
    print("[%s] end convert video to wav, return is %d %s" % (self.gpu_id, status, wav_file))

    #处理时间太长mysql会自动断开
    conn, cur = reconnect_mysql()
    set_processed_flag(cur, conn, id)

    #记录数据到数据库
    print("开始写入wav文件和识别好的字幕信息文件到数据库")
    sql = "insert into wav_and_text (wav_save_ip,wav_class, wav_save_path, subtitle_file_path) values(%s,%s,%s,%s)"
    print(sql % (myip, video_class, wav_file, ocr_merge_record_file ))
    try:
      ret = cur.execute(sql, (myip, video_class, wav_file, ocr_merge_record_file ))
    except:
      traceback.print_exc()
    print("[%s] 写入完成, 改变记录数: %d" % (self.gpu_id, ret))

    cur.close()
    conn.commit()
    conn.close()

    print("[%s] delete files" % (self.gpu_id))
    os.remove(cut_file_path)
    os.remove(snapshot_record_file)
    os.remove(ocr_record_file)
    command = "rm -rf " + " ../snapshot_dir/"+ file_name_prefix
    command = command.encode('utf-8')
    (status, output) = commands.getstatusoutput(command)
    print("[%s] delete complete" % (self.gpu_id))

    WorkThread.sub_current_thread_number()

def run_ocr(cut_video_dir, wav_dir, ocr_merge_record_dir, ocr_record_dir, snapshot_record_dir, is_use_gpu, gpu_id):
  tf_ocr_model_dir = "/asrDataCenter/dataCenter/modelCenter/ocr/ocr_5blstm_manybg"
  tf_model = ocrmodel.OCRModel(tf_ocr_model_dir, is_use_gpu, gpu_id)

  lock = threading.Lock()
  times=0
  maxtimes = 2
  while times < maxtimes:
    time.sleep(5)
    times += 1
    work_thread = WorkThread(lock, gpu_id, cut_video_dir, tf_model, wav_dir, ocr_merge_record_dir, ocr_record_dir, snapshot_record_dir)
    work_thread.start()
    WorkThread.add_current_thread_number()
    print(WorkThread.get_current_thread_number())
    while WorkThread.get_current_thread_number() >= 2:
      time.sleep(1)

  work_thread.join()

  print("ocr process execute over ,exit.....")
  exit(0)
  
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

  cut_video_dir="../cut_video"
  snapshot_record_dir = "../snapshot_record/"
  ocr_record_dir = "../ocr_record"
  ocr_merge_record_dir = "../ocr_merge_record"
  wav_dir = "../wav"
  if not os.path.exists(cut_video_dir):
    os.makedirs(cut_video_dir)
  if not os.path.exists(snapshot_record_dir):
    os.makedirs(snapshot_record_dir)
  
  if not os.path.exists(ocr_record_dir):
    os.makedirs(ocr_record_dir)

  if not os.path.exists(ocr_merge_record_dir):
    os.makedirs(ocr_merge_record_dir)

  wav_dir = os.path.join(os.getcwd(), "wav")
  if not os.path.exists(wav_dir):
    os.makedirs(wav_dir)

  pool = multiprocessing.Pool(processes = processes_number)
  
  for gpu_id in use_gpus_list:
    time.sleep(10)
    pool.apply_async(run_ocr,(cut_video_dir, wav_dir, ocr_merge_record_dir, ocr_record_dir, snapshot_record_dir, is_use_gpu, gpu_id ))
  pool.close()  
  pool.join()  



