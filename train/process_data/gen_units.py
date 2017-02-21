#coding=utf-8

#读取训练数据的所有的label的文本，提取出来每个字符，然后给个序号

import codecs



text_file="../text/origin.txt"
output_units_file="./output/units.txt"
chardict={}
with codecs.open(text_file,'r','utf-8') as fr:
  for line in fr:
    line = line.strip()
    for char in line:
      if char != " ":
        chardict[char]=1

with codecs.open(output_units_file,'w','utf-8') as fw:
  i = 0
  for char in chardict:
    fw.write("%s %d\n"%(char,i))
    i += 1
