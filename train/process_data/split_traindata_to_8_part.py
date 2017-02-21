#coding=utf-8

import os

traindata_dir="./output/"

feature_file=os.path.join(traindata_dir, "allimg.cvs")
label_file=os.path.join(traindata_dir, "alllabel")

example_number = 4082400

split_number = 8
onefile_number = int(example_number / split_number) + 1

split_dir="./split_dir"
for i in range(split_number):
  tempdir = split_dir+"_"+str(i)
  if not os.path.exists(tempdir):
    os.makedirs(tempdir)


with open(feature_file, 'r', encoding="utf-8") as feature_fr, \
   open(label_file, 'r', encoding="utf-8") as label_fr:
  write_line_number = 0
  i = 0
  wpath = split_dir+"_"+str(i)
  ffw = open(os.path.join(wpath, "train.feature"), 'w', encoding="utf-8")
  lfw = open(os.path.join(wpath, "train.label"), 'w', encoding="utf-8")
  while True:
    feature_line=feature_fr.readline()
    label_line=label_fr.readline()

    if feature_line == "":
      break
    
    ffw.write(feature_line)
    lfw.write(label_line)

    write_line_number += 1

    if write_line_number>=onefile_number:
      write_line_number = 0
      i+=1
      ffw.close()
      lfw.close()

      wpath = split_dir+"_"+str(i)
      ffw = open(os.path.join(wpath, "train.feature"), 'w', encoding="utf-8")
      lfw = open(os.path.join(wpath, "train.label"), 'w', encoding="utf-8")


ffw.close()
lfw.close()



