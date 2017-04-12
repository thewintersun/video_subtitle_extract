#coding=utf-8
from PIL import Image,ImageDraw,ImageFont
import os
import cv2

def embed_char_to_img(input_img_file,output_img_file, text, font_file, font_size, 
                    x, y, fill_color, shadow_color, shadow_size=1, thicker_border=True, side_shadow=False):
  '''将文字嵌入到图片中
  
  params:
    side_shadow: 是否只有右边，下边有阴影
  '''

  font = ImageFont.truetype(font_file, font_size)
  img = Image.open(input_img_file)  
  draw = ImageDraw.Draw(img)

  if side_shadow == False:
    # thin border
    for i in range(1, shadow_size+1):
      draw.text((x-i, y), text, font=font, fill=shadow_color)
      draw.text((x+i, y), text, font=font, fill=shadow_color)
      draw.text((x, y-i), text, font=font, fill=shadow_color)
      draw.text((x, y+i), text, font=font, fill=shadow_color)

    # thicker border
    if thicker_border == True:
      for i in range(1, shadow_size+1):
        draw.text((x-i, y-i), text, font=font, fill=shadow_color)
        draw.text((x+i, y-i), text, font=font, fill=shadow_color)
        draw.text((x-i, y+i), text, font=font, fill=shadow_color)
        draw.text((x+i, y+i), text, font=font, fill=shadow_color)
  else:
    # thin border
    for i in range(1, shadow_size+1):
      draw.text((x+i, y), text, font=font, fill=shadow_color)
      draw.text((x, y+i), text, font=font, fill=shadow_color)

    # thicker border
    if thicker_border == True:
      for i in range(1, shadow_size+1):
        draw.text((x+i, y+i), text, font=font, fill=shadow_color)

  draw.text((x, y), text, font=font, fill=fill_color)

  img.save(output_img_file,'JPEG')

def cut_img(input_img_file, output_img_file, left, upper, right, lower):
  ''' 从图片中裁剪出来字幕'''
  img = Image.open(input_img_file)
  region = (left, upper, right, lower)

  #裁切图片
  cropImg = img.crop(region)

  #保存裁切后的图片
  cropImg.save(output_img_file)

def img_white_ratio(img_file):
  img = cv2.imread(img_file, -1)
  gray_img = cv2.cvtColor(img, cv2.cv.CV_BGR2GRAY)
  num = 0
  for i in range(gray_img.shape[0]):
    for j in range(gray_img.shape[1]):
      if gray_img[i][j] > 210 and gray_img[i][j]!= 255:
        num += 1

  return num*1.0 / gray_img.size



if __name__ == "__main__":
  pass
  times = 0
  picdir="../data/pic"
  ratio_dict = {}
  for i in range(10):
    ratio_dict[i] = 0
  for f in os.listdir(picdir):
    times +=1
    if times > 10000:
      break
    picfile = os.path.join(picdir, f)
    ratio = img_white_ratio(picfile)
    r = int(ratio * 10) 
    ratio_dict[r] = ratio_dict[r] + 1
    

  for a in  ratio_dict:
    print(a, ratio_dict[a])
