#coding=utf-8

#将图片先进行灰度处理，然后按照列展开， 变成一行数据

import cv2
import codecs
import numpy as np

textfile="./split_dir_1/train.feature"
pic_dir="./data/pic/allpic/"

units_file="./output/units.txt"
cvs_file="./output/img.cvs"
label_file="./output/label"

def img2cvs(img_file ):
  img_file = img_file.encode('utf-8')
  img = cv2.imread(img_file, -1)
  gray_img = cv2.cvtColor(img, cv2.cv.CV_BGR2GRAY)
  trans_img = np.transpose(gray_img)

  row_list = []
  for line in trans_img:
    str_list = [str(i) for i in line]
  
    row_list.append(",".join(str_list))

  return " ".join(row_list)



with codecs.open(textfile,'r','utf-8') as text_reader,\
  codecs.open(units_file, 'r','utf-8') as units_fr, \
  codecs.open(cvs_file, 'w','utf-8') as cvs_fw, \
  codecs.open(label_file, 'w','utf-8') as label_fw:

  #清空文件
  cvs_fw.truncate()

  unit_dict = {}
  for line in units_fr:
    unit_char,unit_index = line.strip().split()
    unit_dict[unit_char] = unit_index
  

  for line in text_reader:
    line = line.strip()
    line_split = line.split()
    pic_file_prefix = line_split[0]
    text = line_split[1]
    
    pic_file_path = pic_dir + pic_file_prefix + ".jpg"

    img_data = img2cvs(pic_file_path)
    cvs_fw.write(img_data + '\n')

    labels = []
    for t in text:
      unit = unit_dict[t]
      labels.append(unit)
    label_fw.write(" ".join(labels) + "\n")



