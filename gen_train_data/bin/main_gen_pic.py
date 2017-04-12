#coding=utf-8
import img_utils
import os
import codecs
import cv2
import threading
import time
import multiprocessing
from multiprocessing import Pool, Lock, Value  


	
def gen_pic(number_id, img_file, text, font_file, font_size, x, y , fill_color, shadow_color, output_img_file, fontfilename, margin_data, side_shadow):
  
  font_height = 38
  subtitle_width = 730

  temp_embed_img_file ="./temp."+ str(number_id) + ".jpg"
  img_utils.embed_char_to_img(img_file, temp_embed_img_file, text, font_file, font_size,
              x, y, fill_color, shadow_color, side_shadow=side_shadow)

  vertical_top_offset = 0
  vertical_bottom_offset = 0
  #如果是msyhdb, msyh偏移量要变化
  if fontfilename=="msyhbd.ttf" or fontfilename=="msyh.ttf":
    vertical_top_offset = -7
    vertical_bottom_offset = -7

  #生成各种不同样子的字幕

  vertical_top_offset = vertical_top_offset + margin_data[0]
  vertical_bottom_offset = vertical_bottom_offset - margin_data[1]
    
  cut_left = 150-10
  cut_upper = y - vertical_top_offset
  cut_lower = y + font_height - vertical_bottom_offset
  cut_height = cut_lower - cut_upper

  #保持 38*730的比例
  cut_width = int(subtitle_width * (float(cut_height)/ font_height))
  cut_rigth = cut_left + cut_width
  
  img_utils.cut_img(temp_embed_img_file, output_img_file,  cut_left, cut_upper, cut_rigth, cut_lower)
  
  img = cv2.imread(output_img_file, -1)
  resize_img = cv2.resize(img,(subtitle_width,font_height))
  cv2.imwrite(output_img_file, resize_img)


  os.remove(temp_embed_img_file)

  return output_img_file + "\t" + text + '\t' + fontfilename

def write_file_callback(line):
  print(line)
  record_dir="../data/record/"
  record_file = os.path.join(record_dir, "pic_and_text.record")

  with codecs.open(record_file, 'a', 'utf-8') as fw:
    fw.write(line + '\n')



current_thread_number = 0
class WorkThread(threading.Thread):
  def __init__(self, thread_id, img_file, text, font_file, font_size,
              x, y, fill_color, shadow_color, output_img_file,fontfile, margin_data, fw):
    threading.Thread.__init__(self)
    self.thread_id = thread_id
    self.img_file = img_file
    self.text = text
    self.font_file = font_file
    self.font_size = font_size
    self.x = x
    self.y = y
    self.fill_color = fill_color
    self.shadow_color = shadow_color
    self.output_img_file = output_img_file
    self.fontfile = fontfile
    self.margin_data = margin_data
    self.fw = fw

  def run(self):
    global current_thread_number
    font_height = 38
    subtitle_width = 730

    temp_embed_img_file ="./temp."+self.thread_id + ".jpg"
    img_utils.embed_char_to_img(self.img_file, temp_embed_img_file, self.text, self.font_file, self.font_size,
              self.x,self.y, self.fill_color, self.shadow_color)

    vertical_top_offset = 3
    vertical_bottom_offset = 3
    #如果是msyhdb, msyh偏移量要变化
    if self.fontfile=="msyhbd.ttf" or self.fontfile=="msyh.ttf":
      vertical_top_offset = -4
      vertical_bottom_offset = -4

    #生成各种不同样子的字幕

    vertical_top_offset = vertical_top_offset + self.margin_data[0]
    vertical_bottom_offset = vertical_bottom_offset - self.margin_data[1]
    
    cut_left = 150-10
    cut_upper = self.y - vertical_top_offset
    cut_lower = self.y + font_height - vertical_bottom_offset
    cut_height = cut_lower - cut_upper

	#保持 38*730的比例
    cut_width = int(subtitle_width * (float(cut_height)/ font_height))
    cut_rigth = cut_left + cut_width
    img_utils.cut_img(temp_embed_img_file,self.output_img_file,  cut_left, cut_upper, cut_rigth, cut_lower)
    img = cv2.imread(self.output_img_file, -1)
    resize_img = cv2.resize(img,(subtitle_width,font_height))
    cv2.imwrite(self.output_img_file, resize_img)
    print(self.output_img_file)
    self.fw.write(output_img_file + "\t" + self.text + '\t' + self.fontfile + '\n')
    current_thread_number -= 1
    os.remove(temp_embed_img_file)

if __name__=="__main__":
  picdir="../videopic"

  fontdir="../../fonts/"
  textfile = '../data/text/filter.txt'

  output_pic_dir="../data/pic/"

  record_dir="../data/record/"

  picfiles = os.listdir(picdir)
  picfile_num = len(picfiles)
  picfile_index = 0

  fontfiles = os.listdir(fontdir)
  fontfile_num = len(fontfiles)
  fontfile_index = 0

  pos_list=[]
  pos_list.append((150,50))
  pos_list.append((155,100))
  pos_list.append((150,150))
  pos_list.append((160,50))
  pos_list.append((165,100))
  pos_list.append((160,150))
  pos_list.append((170,50))
  pos_list.append((170,100))
  pos_list.append((170,150))
  pos_list.append((180,75))
  pos_list.append((180,100))
  pos_list.append((190,50))
  pos_list.append((190,100))
  pos_list.append((190,150))
  pos_list.append((200,200))
  pos_list.append((210,100))
  pos_list.append((210,250))
  pos_list.append((220,250))
  pos_list.append((220,50))
  pos_list.append((220,150))
  pos_list_size = len(pos_list)
  pos_index = 0
  
 

 
  
  
  margin_list = []
  #表示字体截取的时候距离上面空隙和下面的空隙
  margin_list.append((0,0))
  margin_list.append((0,2))
  margin_list.append((0,4))
  margin_list.append((0,6))
  margin_list.append((0,8))
  margin_list.append((0,10))
  margin_list.append((0,12))
  margin_list.append((0,14))
  margin_list.append((2,0))
  margin_list.append((2,2))
  margin_list.append((2,4))
  margin_list.append((2,6))
  margin_list.append((2,8))
  margin_list.append((2,10))
  margin_list.append((2,12))
  margin_list.append((2,14))
  margin_list.append((4,0))
  margin_list.append((4,2))
  margin_list.append((4,4))
  margin_list.append((4,6))
  margin_list.append((4,8))
  margin_list.append((4,10))
  margin_list.append((4,12))
  margin_list.append((4,14))
  margin_list.append((6,0))
  margin_list.append((6,2))
  margin_list.append((6,4))
  margin_list.append((6,6))
  margin_list.append((6,8))
  margin_list.append((6,10))
  margin_list.append((6,12))
  margin_list.append((6,14))
  margin_list.append((8,0))
  margin_list.append((8,2))
  margin_list.append((8,4))
  margin_list.append((8,6))
  margin_list.append((8,8))
  margin_list.append((8,10))
  margin_list.append((8,12))
  margin_list.append((8,14))
  margin_list.append((10,0))
  margin_list.append((10,2))
  margin_list.append((10,4))
  margin_list.append((10,6))
  margin_list.append((10,8))
  margin_list.append((10,10))
  margin_list.append((10,12))
  margin_list.append((10,14))
  margin_list.append((12,0))
  margin_list.append((12,2))
  margin_list.append((12,4))
  margin_list.append((12,6))
  margin_list.append((12,8))
  margin_list.append((12,10))
  margin_list.append((12,12))
  margin_list.append((12,14))
  margin_list.append((14,0))
  margin_list.append((14,2))
  margin_list.append((14,4))
  margin_list.append((14,6))
  margin_list.append((14,8))
  margin_list.append((14,10))
  margin_list.append((14,12))
  margin_list.append((14,14))
  margin_size = len(margin_list)
  margin_index = 0

  
  if not os.path.exists(output_pic_dir):
    os.mkdir(output_pic_dir) 
  if not os.path.exists(record_dir):
    os.mkdir(record_dir) 

  record_file = os.path.join(record_dir, "pic_and_text.record")

  fill_color=(255,255,255) 

  shadow_color_list =[]
  shadow_color_list.append((0,0,0))
  shadow_color_list.append((25,25,25))
  shadow_color_list.append((50,50,50))
  shadow_color_list.append((100,100,100))

  shadow_color_size = len(shadow_color_list)
  shadow_color_index = 0

  side_shadow_list = []
  side_shadow_list.append(True)
  side_shadow_list.append(False)
  side_shadow_size = len(side_shadow_list)
  side_shadow_index = 0

  font_size=36


  output_pic_prefix = 0
  line_number = 0
  max_thread_number = 100
  
  pool = multiprocessing.Pool(processes = 24)   
  if os.path.exists(record_file):
    os.remove(record_file)
    pass
  with codecs.open(textfile, 'r','utf-8') as fr:
    a = 0
    for line in fr:
      a += 1
      text = line.strip()
    
      img_file = os.path.join(picdir, picfiles[picfile_index])
      font_file= os.path.join(fontdir, fontfiles[fontfile_index])

      pos = pos_list[pos_index]
      x = pos[0]
      y = pos[1]

      shadow_color = shadow_color_list[shadow_color_index]
      side_shadow = side_shadow_list[side_shadow_index]
      

      margin_data = margin_list[margin_index]
      output_img_file = os.path.join(output_pic_dir, str(output_pic_prefix)+".jpg")

      thread_id = line_number % max_thread_number
      pool.apply_async(gen_pic,(str(thread_id), img_file, text, font_file, font_size, x, y, fill_color, \
                     shadow_color, output_img_file,fontfiles[fontfile_index], margin_data,side_shadow, ), callback=write_file_callback)
     

      '''
      work_thread = WorkThread(str(thread_id), img_file, text, font_file, font_size,
              x, y, fill_color, shadow_color, output_img_file,fontfiles[fontfile_index], margin_data, fw)
      work_thread.start()
      #print(current_thread_number)
      current_thread_number += 1
      while current_thread_number >= max_thread_number:
        time.sleep(0.1)
      '''
      fontfile_index = (fontfile_index + 1) % fontfile_num
      pos_index = (pos_index + 1) % pos_list_size
      output_pic_prefix += 1
  
      margin_index = (margin_index + 1) % margin_size
      shadow_color_index = (shadow_color_index + 1) % shadow_color_size
      side_shadow_index = (side_shadow_index + 1) % side_shadow_size

      if pos_index == 0:
        picfile_index = (picfile_index + 1) % picfile_num
      line_number += 1
    '''
    work_thread.join()
    time.sleep(5)
    '''
    pool.close()  
    pool.join()  
