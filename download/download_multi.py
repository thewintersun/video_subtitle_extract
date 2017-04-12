#coding=utf-8

import argparse
import MySQLdb
import codecs
import traceback
import commands
import os
import sys
import time
import threading
reload(sys)
sys.setdefaultencoding('utf8')


def is_ustr(in_str):
    out_str=''
    for i in range(len(in_str)):
        if is_uchar(in_str[i]):
            out_str=out_str+in_str[i]
        else:
            out_str=out_str+''
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


table_name="iqiyi_list"
myip="127.0.0.1"
video_class_list = []

config_file= "config/config"
with codecs.open(config_file, 'r', 'utf-8') as fr:
  for line in fr:
    if line.startswith("#"):
      continue
    w1,w2 = line.strip().split('    ') 
    if w1 == "localip":
      myip = w2



current_thread_number = 0
max_thread_num=5

class WorkThread(threading.Thread):
  def __init__(self, lock, table_name, video_class):
    threading.Thread.__init__(self)
    self.lock = lock
    self.table_name = table_name
    self.video_class = video_class

  def run(self):
    global current_thread_number

    conn,cur = reconnect_mysql()
    self.lock.acquire()

    video_class_list = []
    cur.execute("select Id,  video_class from subtitle_pos")
    db_result = cur.fetchall()
    for Id,  video_class in db_result:
      video_class_list.append(video_class.strip())


    video_class_condition = "(video_class='"+ video_class_list[0]+"'"
    for i in range(1, len(video_class_list)):
      video_class_condition += "or video_class='" + video_class_list[i] +"'"
    video_class_condition += ")"

    result_number = cur.execute("select Id, video_class,title,url from "+ \
      self.table_name + " where is_download = 0 and is_downloading=0 and "+ video_class_condition
      +" order by Id asc limit 1")
    if result_number == 0:
      print("all url in database is downloaded, exit")
      cur.close()
      conn.commit()
      conn.close()
      current_thread_number -= 1
      self.lock.release()
      return
  
    db_result = cur.fetchone() 
    id = db_result[0]
    video_class = db_result[1].strip()
    title = db_result[2].strip()
    url = db_result[3].strip()

    #如果title中包含预告等字样
    if title.find("预告") != -1:
      print("find yugao in title string, jump it ! %s " % title)
      sql = "update " + self.table_name + " set is_downloading=2 where Id="+str(id)
      ret = cur.execute(sql)
      conn.commit()
      cur.close()
      conn.close()
      current_thread_number -= 1
      self.lock.release()
      return

    sqli="update " + self.table_name + " set is_downloading=1 where Id="+str(id)
    ret = cur.execute(sqli)
    conn.commit()
    cur.close()
    conn.close()
    self.lock.release()

    # downloading
    save_dir = os.path.join(os.getcwd(),"video")
    if not os.path.exists(save_dir):
      os.makedirs(save_dir)

    title = is_ustr(title)
    print('./download_video.sh ' + url + save_dir+ " " + title)
    (status, output) = commands.getstatusoutput('./download_video.sh ' + url +" " +  save_dir + " " + title)

    
    #可能下载时间过长
    conn,cur = reconnect_mysql()
    if status == 0:
      #标记下载完成
      #下载成功，更新保存路径
      filepath= os.path.join(save_dir, title+".mp4")
      sqli="update " + self.table_name + " set is_downloading=0,is_download=1, save_ip='" + myip + "', save_path='"+filepath+"'  where Id="+str(id)
      ret = cur.execute(sqli)
      conn.commit() 

    else:
      if status/256 == 1:
        print("you-get error jump this video")
        sqli = "update " + self.table_name + " set is_downloading=-1 where Id="+str(id) 
      else:
        #去掉downloading标记
        sqli="update " + self.table_name + " set is_downloading=0 where Id="+str(id) 
      ret = cur.execute(sqli)
      conn.commit()  

    cur.close()
    conn.commit()
    conn.close()
    current_thread_number -= 1


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("video_class", help="display a square of a given number", type=str)

  args = parser.parse_args()

  video_class = args.video_class


  lock = threading.Lock()
  times=0
  maxtimes = 50
  while times < maxtimes:
    times += 1
    work_thread = WorkThread(lock, table_name, video_class)
    work_thread.start()
    print(current_thread_number)
    current_thread_number += 1
    while current_thread_number >= max_thread_num:
      time.sleep(0.1)

  print("wait for last thread .....%d" % current_thread_number)
  work_thread.join()
  time.sleep(5)


