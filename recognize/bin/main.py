#coding=utf-8
import ocrmodel
import codecs
import time

def maybe_same(str1,str2):
  '''判断2个字符串是否可能是相同的'''
  if len(str1) > len(str2):
    temp = str1
    str1 = str2
    str2 = temp

  same_number = 0
  for i in range(len(str1)):
    for j in range(len(str2)):
      if str1[i] == str2[j]:
        same_number += 1

  if float(same_number)/ len(str1) > 0.3:
    return True
  else:
    return False


def is_contain_num_alph(in_str):
  '''判断字符串中是否包含了数字和字母'''
  if len(in_str) == 1:
    return True
  for i in range(len(in_str)):
    uchar = in_str[i]
    if uchar >=u'\u0030' and uchar <=u'\u0039':
      return True
    if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
      return True
  return False





if __name__ == "__main__":
  model_dir="/asrDataCenter/dataCenter/modelCenter/ocr/ocr_990"
  snapshot_record_file="../record/snapshot.record"
  recognize_record_file="../record/recognize.record"

  model = ocrmodel.OCRModel(model_dir)

  with codecs.open(snapshot_record_file, 'r','utf-8') as fr, \
    codecs.open(recognize_record_file, 'w', 'utf-8') as fw:
    last_sentence = ""
    last_subtitle_start_time = 0
    last_subtitle_end_time = 0
    last_video_file = ""

    # 是否一句话产生了不同的文字
    is_maybe_same_with_last = False

    for line in fr:
      print(time.time())
      video_file, snap_time, pic_file = line.strip().split() 
      recognize_sentence = model.pic_to_char(pic_file)
      recognize_sentence = ''.join(recognize_sentence)
     
      #这句话没有字幕 
      if recognize_sentence=="" or len(recognize_sentence)==0:
        # 上一句话有字幕, 则写入上一句
        if last_sentence != "":
          #如果上一句没有发生过字幕识别不准,则写入
          if is_maybe_same_with_last == False:
            if not (is_contain_num_alph(last_sentence) and len(last_sentence)<6):
              output_str = last_video_file+'\t'+ last_subtitle_start_time + \
                '\t' + last_subtitle_end_time +'\t' + last_sentence + '\n'
              fw.write(output_str)
          
          last_sentence = ""
          last_subtitle_start_time = 0
          last_subtitle_end_time = 0
          last_video_file = video_file
          is_maybe_same_with_last = False
        else:
          #如果上一句也没字幕
          continue

      # 这一句有内容，并且和上一句一样
      if recognize_sentence != "" and recognize_sentence == last_sentence:
        last_subtitle_end_time = snap_time

      #这一句有内容，和上一句不一样
      if recognize_sentence != "" and recognize_sentence != last_sentence:
        # 如果上一句是空
        if last_sentence == "":
          last_subtitle_start_time = snap_time
          last_subtitle_end_time = snap_time
          last_sentence = recognize_sentence
          last_video_file = video_file       
        else:
          #如果上一句是另外一句
          
          #计算是否可能是同一句话
          if maybe_same(recognize_sentence, last_sentence):
            #如果是相同的,说明识别不确定
            is_maybe_same_with_last = True
          else:
            #如果是另外一句，并且前面的字幕没发生过识别不确定
            if is_maybe_same_with_last == False:
              if not (is_contain_num_alph(last_sentence) and len(last_sentence)<6):
                output_str = last_video_file+'\t'+ last_subtitle_start_time + \
                    '\t' + last_subtitle_end_time +'\t' + last_sentence + '\n'
                fw.write(output_str)
        
            last_subtitle_start_time = snap_time
            last_subtitle_end_time = snap_time
            last_sentence = recognize_sentence
            last_video_file = video_file
            is_maybe_same_with_last = False

        
        
      
  
