#coding=utf-8

import os

def rm_no_change_pic():
  video_pic_dir = "../videopic/"
  rm_number = 0
  for file in os.listdir(video_pic_dir):
    if "change" not in file:
      filepath = video_pic_dir + file
      os.remove(filepath)
      rm_number += 1
      if rm_number > 30000:
        break

if __name__ == "__main__":
  rm_no_change_pic()
