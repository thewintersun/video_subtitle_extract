#coding=utf-8

import codecs

subtitle_head_file = "./subtitle_head"

input_text_file = "./text/origin.txt"

output_subtitle_dir = "./output_subtitle/"

output_subtitle_file_suffix_number = 0

max_dialogue_number = 7200 # 一个文件多少条字幕
dialogus_interval_ms = 25  #多少毫秒一个字幕
current_number = 0 # 当前处理多少行文本

start_ms = 1000

def read_subtitle_head(file):
  fr = codecs.open(file,'r','utf-8')
  lines = fr.readlines()
  fr.close()
  return ''.join(lines)

def get_time_str(ms):
  # 毫秒转换成ass格式里面的时间的格式字符串
  s = ms / 100
  ms_str= "%02d" % (ms %100)
  s_str = "%02d" % (s%60)
  m = s / 60
  m_str = "%02d" % (m%60)
  h = m / 60
  h_str = "%02d" % (h%24)
  d = h / 24
  d_str = "%01d" % (d%1)

  return h_str + ":" + m_str + ":" + s_str +"."+ms_str



if __name__ == '__main__':
  write_filename = output_subtitle_dir+str(output_subtitle_file_suffix_number)+".ass"
  sub_fw = codecs.open(write_filename, 'w','utf-8')
  subtitle_head = read_subtitle_head(subtitle_head_file)
  sub_fw.write(subtitle_head)
  current_ms = start_ms

  with codecs.open(input_text_file,'r','utf-8') as text_fr:
    for line in text_fr:
      start_time = get_time_str(current_ms)
      end_time = get_time_str(current_ms + dialogus_interval_ms - 1)
      write_line = "Dialogue: 0," + start_time + "," + end_time + ",*Default,NTP,0000,0000,0000,," + line.strip() + "\n"
      sub_fw.write(write_line)

      current_number += 1
      current_ms += dialogus_interval_ms
      if current_number % max_dialogue_number == 0:
        #写完了一个文件
        sub_fw.close()
        output_subtitle_file_suffix_number += 1
        write_filename = output_subtitle_dir+str(output_subtitle_file_suffix_number)+".ass"
        print("write to file %s\n"% write_filename)
        sub_fw = codecs.open(write_filename, 'w','utf-8')
        sub_fw.write(subtitle_head)
        current_ms = start_ms

  sub_fw.close()



      
    




    
