#coding=utf-8
import sys
import re
import codecs

def is_ustr(in_str):
    out_str=''
    for i in range(len(in_str)):
        if is_uchar(in_str[i]):
            out_str=out_str+in_str[i]
        else:
            out_str=out_str+' '
    return out_str
def is_uchar(uchar):
    """判断一个unicode是否是汉字"""
    if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
            return True
    """判断一个unicode是否是数字"""
    if uchar >= u'\u0030' and uchar<=u'\u0039':
            return True        
    """判断一个unicode是否是英文字母"""
    if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
            return True
    #if uchar in ('-',',','，','。','.','>','?'):
    #        return True
    return False


if __name__ == '__main__':
  inputfile = "./text"
  outputfile = "./origin2.txt"
  with codecs.open(inputfile, 'r', 'utf-8') as fr, \
      codecs.open(outputfile,'w', 'utf-8') as fw:
    for line in fr:
      line = line.strip()
      filter_line = is_ustr(line)
      line_list = filter_line.split()
      for l in line_list:
        if len(l) >2 and len(l)<=25:
          fw.write(l+"\n")

