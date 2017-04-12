#coding=utf-8

import commands
import argparse
import MySQLdb
import traceback
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

def scp_and_changdb(video_class, myip):
  
  conn,cur = reconnect_mysql()


  try:
    sql2 = "select save_ip,save_path,Id from iqiyi_list where video_class='" + video_class + "' and is_download=1 and is_downloading=0 and save_ip!='"+myip+"'"
    #print(sql2)
    ret = cur.execute(sql2)
    if ret == 0:
      print("not video_class find in database, video_class is %s" % video_class)
      cur.close()
      conn.close()
      return
    db_result = cur.fetchone()
    save_ip = db_result[0]
    save_path = db_result[1]
    id = db_result[2]
    # scp 文件
    command = "scp " + save_ip + ":" + save_path + " " + save_path
    #print(command)
    command = command.encode('utf-8')
    (status, output) = commands.getstatusoutput(command)
    if status != 0:
      print("scp error %s " %  command)
      #如果scp错误，说明没有文件，则更新数据库记录
      sql = "update iqiyi_list set is_download=0,is_downloading=0,save_ip='', save_path='' where Id=" +str(id)
      ret = cur.execute(sql)
      if ret == 0:
        print("update db error %s" % sql)
        cur.close()
        conn.close()
        return
      conn.commit()       
      cur.close()
      conn.close()
      return
   #更改数据库
    sql3 = "update iqiyi_list set save_ip='"+ myip + "' where Id="+str(id)
    #print(sql3)
    ret = cur.execute(sql3)
    if ret == 0:
      print("update db error %s" % sql3)
      cur.close()
      conn.close()
      return
    # del 文件
    command = "ssh " + save_ip + " rm " + save_path 
    print(command)
    command = command.encode('utf-8')
    (status, output) = commands.getstatusoutput(command)
    if status != 0:
      print("del file  error %s " % command )
      return
  except:
    traceback.print_exc()

  conn.commit()
  cur.close()
  conn.close()

if __name__ == "__main__":
  myip=read_config()
  parser = argparse.ArgumentParser()
  parser.add_argument("video_class", help="display a square of a given number", type=str)

  args = parser.parse_args()

  video_class = args.video_class

  for i in range(100):
    scp_and_changdb(video_class.decode('utf-8'), myip) 
  
  
  
