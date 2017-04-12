#coding=utf-8
import MySQLdb
import os
import codecs

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


conn, cur = reconnect_mysql()

myip="127.0.0.1"
config_file= "../download/config/config"
with codecs.open(config_file, 'r', 'utf-8') as fr:
  for line in fr:
    if line.startswith("#"):
      continue
    w1,w2 = line.strip().split('    ')
    if w1 == "localip":
      myip = w2


sql="select Id,save_path  from iqiyi_list where video_class not in (select video_class from subtitle_pos) and save_ip='"+myip+"'"
#sql="select Id,save_path  from iqiyi_list where save_ip='"+myip+"'"
result_number = cur.execute(sql)
if result_number == 0:
  print("all wav at this machine is processed, exit this thread")
  cur.close()
  conn.commit()
  conn.close()
  exit(0)

db_result = cur.fetchall()
for Id, save_path in db_result:
  #删除文件
  if os.path.exists(save_path):
    os.remove(save_path)
  #删除mysql
  print(Id, save_path)
  sql = "delete from iqiyi_list where Id="+str(Id)
  cur.execute(sql)

conn.commit()
cur.close()
conn.close()
