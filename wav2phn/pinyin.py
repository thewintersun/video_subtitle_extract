#!/usr/bin/env python3
#coding=utf-8
"""
Created by Eric Lo on 2010-05-20.
Copyright (c) 2010 __lxneng@gmail.com__. http://lxneng.com All rights reserved.
"""

def is_ustr(in_str):
    out_str=''
    for i in range(len(in_str)):
        if is_uchar(in_str[i]):
            out_str=out_str+in_str[i]
        else:
            out_str=out_str+''
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


class Pinyin():
    def __init__(self, data_path='./Mandarin.dat'):
        self.dict = {}
        for line in open(data_path):
            k, v = line.split('\t')
            self.dict[k] = v
        self.splitter = ''

    def get_pinyin(self, chars=u"你好吗"):
        chars = is_ustr(chars)
        result = []
        for char in chars:
            key = "%X" % ord(char)
            #if char is spacekey
            if key =="20":
              continue
            try:
                result.append(self.dict[key].split(" ")[0].strip()[:-1].lower())
            except:
                result.append(char)
        return self.splitter.join(result)

if __name__ =="__main__":
  py= Pinyin()
  print(py.get_pinyin(u"你好啊"))
