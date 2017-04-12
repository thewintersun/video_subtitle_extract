#coding=utf-8

import os
import codecs

traindata_dir="../data/record/"

feature_file=os.path.join(traindata_dir, "pic_and_text.record.shuffle")

n=0
with codecs.open(feature_file, 'r','utf-8') as fr:
  for line in fr:
    n += 1

example_number = n

split_number = 8
onefile_number = int(example_number / split_number) + 1

split_dir="./split_dir"
if not os.path.exists(split_dir):
  os.makedirs(split_dir)

with codecs.open(feature_file, 'r', "utf-8") as feature_fr:
  write_line_number = 0
  i = 0
  wpath = split_dir
  ffw = codecs.open(os.path.join(wpath, "train.record."+str(i)), 'w', "utf-8")
  while True:
    feature_line=feature_fr.readline()

    if feature_line == "":
      break
    
    ffw.write(feature_line)

    write_line_number += 1

    if write_line_number>=onefile_number:
      write_line_number = 0
      i+=1
      ffw.close()

      ffw = codecs.open(os.path.join(wpath, "train.record." + str(i)), 'w', "utf-8")

ffw.close()



