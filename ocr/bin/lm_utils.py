#coding=utf-8

import commands
import codecs
import os

def get_record_text_ppl(record_file):
  ppl_dict = {}

  record_file_dir = "/".join(record_file.split("/")[:-1])
  record_file_name = record_file.split("/")[-1].split(".")[0]
  record_file_suffix = record_file.split("/")[-1].split(".")[-1]

  record_text_file_path = os.path.join(record_file_dir, record_file_name+"_text." + record_file_suffix)
  record_ppl_file_path = os.path.join(record_file_dir, record_file_name+"_ppl."+ record_file_suffix)

  #将record文件的最后一列取出来，后面给语言模型判断是正常句子的概率
  with codecs.open(record_file, 'r','utf-8') as fr, codecs.open(record_text_file_path, 'w', 'utf-8') as fw:
    for line in fr:
      line_splits = line.strip().split()
      if len(line_splits) == 4:
        fw.write(" ".join(line_splits[3]) + '\n')


  command = "./ngram  -ppl " + record_text_file_path + "  -order 3 -lm ../lm/chinese.lm -debug 1 > " +  record_ppl_file_path
  command = command.encode('utf-8')
  (status, output) = commands.getstatusoutput(command)
  if status != 0:
    print("gen ppl file fail %s"% command)
  
  #分析ppl文件，得到每个句子是文本的困惑度
  '''
  ppl文件格式这样：
  妈 妈 来 了
  1 sentences, 4 words, 0 OOVs
  0 zeroprobs, logprob= -7.106332 ppl= 26.37949 ppl1= 59.78372

  '''
  with codecs.open(record_ppl_file_path, 'r', 'utf-8') as fr:
    i = 0
    for line in fr:
      if i % 4 == 0:
        text = "".join(line.strip().split())
      if i % 4 == 2: 
        log = float(line.strip().split()[3])
        ppl_dict[text] = log
      i += 1

  #delete files
  os.remove(record_text_file_path)
  os.remove(record_ppl_file_path)
  return ppl_dict


if __name__ == "__main__":
  d = get_record_text_ppl("./ocr_record/爱来的刚好第1集.record")
  for i in d:
    print(i)
    print(d[i])
