#coding=utf-8
import ocrmodel
import codecs
import time
import os
import Levenshtein
import cv2
import numpy as np

def get_two_value(v):
  if v <100:
    return 0
  else:
    return 255

def is_white(v):
  if v>180 and v<250:
    return 1
  return 0
  
  
def pic_white_ratio(gray_img):
  #图片偏白色部分所占的比例
  total_white_num = 0
  total_num = 1
  for j in range(gray_img.shape[1]):
    last_value = 255
    n = 0
    white_num = 0
    for i in range(gray_img.shape[0]):
      v = get_two_value(gray_img[i][j])
      white_num += is_white(gray_img[i][j])
      if v != last_value:
        n += 1
      last_value = v
    if n >=8:
      total_white_num += white_num
      total_num += gray_img.shape[0]
    #print (j,n)
  return float(total_white_num)/total_num
  


def img2data( img_file ):
  if not os.path.exists(img_file):
    raise Exception("file not exist. %s" % img_file)

  train_pic_height = 38
  train_pic_width = 730

  img = cv2.imread(img_file, -1)
  gray_img = cv2.cvtColor(img, cv2.cv.CV_BGR2GRAY)

  
  height = gray_img.shape[0]
  width  = gray_img.shape[1]

  new_height = train_pic_height
  new_width  = int((float(train_pic_height)/height) * width)

  #拉伸
  gray_img = cv2.resize(gray_img, (new_width,new_height))
  
  if new_width > train_pic_width:
    gray_img = gray_img[:,:train_pic_width]
  
  #计算偏白色的比例
  white_ratio = 0.1
  
  gray_img = np.transpose(gray_img)

  
  
  #填充
  add_feature = np.zeros((train_pic_width - new_width, new_height))
  gray_img = np.concatenate((gray_img, add_feature))
    
  return gray_img, white_ratio


def pic_data_list_to_feature( pic_data_list):
  feature_list = pic_data_list[0]
  seq_len_list = []
  seq_len_list.append(feature_list.shape[0])
  for i in range(1,len(pic_data_list)):
    feature_list = np.concatenate((feature_list, pic_data_list[i]))
    seq_len_list.append(pic_data_list[i].shape[0])
  return feature_list, seq_len_list
  

	
def ocr(model, snapshot_record_file, recognize_record_file):
  batch_size = 50
  with codecs.open(snapshot_record_file, 'r','utf-8') as fr, \
    codecs.open(recognize_record_file, 'w', 'utf-8') as fw:
    
    pic_list = []
    video_file_list = []
    snap_time_list = []
    pic_data_list = []
    white_ratio_list = []

    for line in fr:

      video_file, snap_time, pic_file = line.strip().split()
      if not os.path.exists(pic_file):
        print("file not exists. %s" % pic_file)
        continue
      pic_list.append(pic_file)
      video_file_list.append(video_file)
      snap_time_list.append(snap_time)

      pic_data,white_ratio = img2data(pic_file.encode('utf-8'))
      pic_data_list.append(pic_data)
      
      white_ratio_list.append(white_ratio)

      if len(pic_list) == batch_size:
        pic_feature_list, seq_len_list = pic_data_list_to_feature(pic_data_list)
        recognize_sentence = model.piclist_to_char(pic_feature_list, seq_len_list)
        for i in range(batch_size):
          if i < len(recognize_sentence):
            recognize_text = ''.join(recognize_sentence[i])
            output_str = video_file_list[i] + '\t' + snap_time_list[i] + \
             '\t' + str(white_ratio_list[i]) + '\t' + recognize_text + '\n'
            fw.write(output_str)
            fw.flush()
          else:
            print("recognize_sentence less that batchsize: %d"%len(recognize_sentence))

        pic_list = []
        video_file_list = []
        snap_time_list = []
        pic_data_list = []
        white_ratio_list = []
        
if __name__ == "__main__":
  pass
      
  
