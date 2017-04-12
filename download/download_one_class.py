#coding=utf-8

import MySQLdb
import codecs
import traceback
import commands
import os
import sys
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


table_name="iqiyi_list"
video_class="爱奇艺首页_综艺_中国式相亲"
myip="127.0.0.1"

config_file= "config/config"
with codecs.open(config_file, 'r', 'utf-8') as fr:
  for line in fr:
    if line.startswith("#"):
      continue
    w1,w2 = line.strip().split('    ') 
    if w1 == "localip":
      myip = w2
    if w1 == "table_name":
      table_name = w2
    if w1 == "video_class":
      video_class = w2



times=0
maxtimes = 10
while times < maxtimes:
  times += 1
  conn= MySQLdb.connect(
        host='192.168.100.71',
        port = 3306,
        user='root',
        passwd='luodongri',
        db ='video',
        charset="utf8",)
  cur = conn.cursor()

  result_number = cur.execute("select Id, video_class,title,url from "+table_name + " where is_download = 0 and is_downloading=0 and video_class='"+video_class+"' order by Id asc limit 1")
  if result_number == 0:
    print("all url in database is downloaded, exit")
    cur.close()
    conn.commit()
    conn.close()
    break
  
  db_result = cur.fetchone() 
  id = db_result[0]
  video_class = db_result[1].strip()
  title = db_result[2].strip()
  url = db_result[3].strip()


  sqli="update " + table_name + " set is_downloading=1 where Id="+str(id)
  ret = cur.execute(sqli)
  conn.commit()
  
  # downloading
  save_dir = os.path.join(os.getcwd(),"video")
  if not os.path.exists(save_dir):
    os.makedirs(save_dir)

  title = is_ustr(title)
  print('./download_video.sh ' + url + save_dir + title)
  (status, output) = commands.getstatusoutput('./download_video.sh ' + url +" " +  save_dir + " " + title)
  if status == 0:
    #标记下载完成
    #下载成功，更新保存路径
    filepath= os.path.join(save_dir, title+".mkv")
    sqli="update " + table_name + " set is_downloading=0,is_download=1, save_ip='" + myip + "', save_path='"+filepath+"'  where Id="+str(id)
    ret = cur.execute(sqli)
    conn.commit() 

  else:
    #去掉downloading标记
    sqli="update " + table_name + " set is_downloading=0 where Id="+str(id) 
    ret = cur.execute(sqli)
    conn.commit()  

  cur.close()
  conn.commit()
  conn.close()


