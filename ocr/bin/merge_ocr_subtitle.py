#coding=utf-8
import codecs
import time
import os
import Levenshtein
import commands
import lm_utils

def maybe_same(str1,str2):
  '''判断2个字符串是否可能是相同的'''
  if len(str1) > len(str2):
    temp = str1
    str1 = str2
    str2 = temp

  #如果长度相差太远认为是不同的
  if float(len(str2))/ len(str1) > 2 and len(str1)>=4:
    return False

  #如果编辑距离大于2, 认为不相同
  distance = Levenshtein.distance(str1,str2)
  if distance <= 3 and len(str1)>=10:
    return True
  if distance <= 4 and len(str1)>=13:
    return True
  if distance <= 1 and len(str1)>=5:
    return True
  if distance > 2 and len(str1)<=6:
    return False
  if distance > 3:
    return False

  return True

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

def find_real_subtitle_in_candidata_list(candidate_list,ppl_dict, style="ppl"):
  #需要出现次数最多，和ppl概率最大同时满足的，增加准确率
  ppl_candidate = ""
  max_log = -10000
  for text in candidate_list:
    log = ppl_dict[text]
    if log > max_log:
      max_log = log
      ppl_candidate = text
  
  #从候选list集合中，找出来可能的真实字幕，如果有相同的两句，认为这个是真实的
  max_same_number = 0
  maxtime_candidate = candidate_list[0]
  for i in range(len(candidate_list)):
    same_number = 0 
    for j in range(i+1, len(candidate_list)):
      if candidate_list[i] == candidate_list[j]:
        same_number += 1
    if max_same_number < same_number:
      max_same_number = same_number
      maxtime_candidate = candidate_list[i]
  #如果没有相同的出现
  if max_same_number == 0 or maxtime_candidate != ppl_candidate:
    return ""

  return maxtime_candidate


def merge_record(record_file, merged_record_file):

  ppl_dict = lm_utils.get_record_text_ppl(record_file)

  with codecs.open(record_file, 'r','utf-8') as fr, \
    codecs.open(merged_record_file, 'w', 'utf-8') as fw:
    last_subtitle = ""
    subtitle_candidate_list = []
    last_subtitle_start_time = 0
    last_subtitle_end_time = 0
    last_video_file = ""

    for line in fr:
      line_splits = line.strip().split('\t')
      if len(line_splits) == 4:
        video_file = line_splits[0]
        snap_time = line_splits[1]
        subtitle = line_splits[3]

      if len(line_splits) == 3:
        video_file = line_splits[0]
        snap_time = line_splits[1]
        subtitle = ""
      
      #这句话没有字幕 
      if subtitle =="":
        # 上一句话有字幕, 则写入上一句
        if last_subtitle != "":
          candidate = find_real_subtitle_in_candidata_list(subtitle_candidate_list, ppl_dict)
          if candidate != "":
            #如果找到了候选字幕
            if (not is_contain_num_alph(candidate)) and len(candidate)>=4:
              if float(last_subtitle_end_time) - float(last_subtitle_start_time)<5.0:
                output_str = last_video_file+'\t'+ last_subtitle_start_time + \
                  '\t' + last_subtitle_end_time +'\t' + candidate + '\n'
                fw.write(output_str)
                fw.flush()
          
          last_subtitle = ""
          last_subtitle_start_time = 0
          last_subtitle_end_time = 0
          last_video_file = video_file
          subtitle_candidate_list = []
        else:
          #如果上一句也没字幕
          continue

      # 这一句有内容，并且和上一句一样
      if subtitle != "" and subtitle == last_subtitle:
        last_subtitle_end_time = snap_time
        subtitle_candidate_list.append(subtitle)

      #这一句有内容，和上一句不一样
      if subtitle != "" and subtitle != last_subtitle:
        # 如果上一句是空
        if last_subtitle == "":
          last_subtitle_start_time = snap_time
          last_subtitle_end_time = snap_time
          last_subtitle = subtitle
          last_video_file = video_file

          subtitle_candidate_list.append(subtitle)
        else:
          #如果上一句是另外一句
          
          #计算是否和上一句相似
          if maybe_same(subtitle, last_subtitle):
            subtitle_candidate_list.append(subtitle)

            last_subtitle_end_time = snap_time
            last_subtitle = subtitle

          else:
            #如果是另外一句
            candidate = find_real_subtitle_in_candidata_list(subtitle_candidate_list, ppl_dict)
            if candidate != "":
              #如果找到了候选字幕
              if (not is_contain_num_alph(candidate)) and len(candidate)>=4:
                if float(last_subtitle_end_time) - float(last_subtitle_start_time)<5.0:
                  output_str = last_video_file+'\t'+ last_subtitle_start_time + \
                    '\t' + last_subtitle_end_time +'\t' + candidate + '\n'
                  fw.write(output_str)
                  fw.flush()

            last_subtitle_start_time = snap_time
            last_subtitle_end_time = snap_time
            last_subtitle = subtitle
            last_video_file = video_file
            subtitle_candidate_list = []
            subtitle_candidate_list.append(subtitle)
      
      

if __name__ == "__main__":
  pass
  record_file = "./ocr_record/女生家长歧视单亲家庭遭金星怒怼.record"
  merged_record_file = "./merge.result"
  merge_record(record_file, merged_record_file)
