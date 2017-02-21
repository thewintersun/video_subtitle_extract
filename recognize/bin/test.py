#coding=utf-8
import cv2
import numpy as np

import Levenshtein

def maybe_same(str1,str2):
  '''判断2个字符串是否可能是相同的'''
  str1 = str1.decode("utf-8")
  str2 = str2.decode("utf-8")
 
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

a="你好啊说明说明说明"
c="你是否"
b="你安慰"
print(maybe_same(a,b))
