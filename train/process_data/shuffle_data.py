#coding=utf-8

import shutil
import os

def shuffle_file(input_file, output_file):
  print("start shuffle file " + input_file)
  split_file_number = 10
  temp_dir = "./temp/"
  if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

  fw = []
  for i in range(split_file_number):
    write_file = os.path.join(temp_dir,"temp."+str(i))
    fw.append(open(write_file, 'w', encoding="utf-8"))

  write_index = 0
  i = 0
  with open(input_file, 'r', encoding="utf-8") as input_fr:
    for line in input_fr:
      fw[i].write(line)
      i+=1
      i = i % split_file_number

  for f in fw:
    f.close()

  #read
  fr = []
  for i in range(split_file_number):
    read_file = os.path.join(temp_dir,"temp."+str(i))
    fr.append(open(read_file, 'r', encoding="utf-8"))

  with open(output_file, 'w', encoding="utf-8") as output_fw:
    for read_index in range(split_file_number):
      for line in fr[read_index]:
        output_fw.write(line)

  for f in fr:
    f.close()

  #删除目录
  shutil.rmtree("./temp",True)

  print("shuffle file complete, output file is " + output_file)

if __name__=="__main__":
  f = "./data/text/alltxt/all.txt"
  shuffle_file(f,f + ".1")
  shuffle_file(f + ".1", f + ".2")
  shuffle_file(f + ".2", f + ".1")
  shuffle_file(f + ".1", f + ".2")
  shuffle_file(f + ".2", f + ".1")
  shuffle_file(f + ".1", f + ".2")
  shuffle_file(f + ".2", f + ".1")
  shuffle_file(f + ".1", f + ".2")
