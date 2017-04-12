#coding=utf-8
import cv2
import numpy as np
import os
import multiprocessing
from multiprocessing import Pool, Lock, Value  


video_dir="../videopic/"

def vpic(filepath,color):
  img = np.ones([720,1280,3], np.uint8) * (color)
  for c in range(img.shape[0]):
    for i in range(img.shape[1]):
      for j in range(img.shape[2]):
        if i % 20 <6:
          img[c][i][j] = 0
  cv2.imwrite(filepath,img)

def hpic(filepath,color):
  img = np.ones([720,1280,3], np.uint8) * (color)
  for c in range(img.shape[0]):
    for i in range(img.shape[1]):
      for j in range(img.shape[2]):
        if c % 20 <6:
          img[c][i][j] = 0
  cv2.imwrite(filepath,img)

def vhpic(filepath, color):
  img = np.ones([720,1280,3], np.uint8) * (color)
  for c in range(img.shape[0]):
    for i in range(img.shape[1]):
      for j in range(img.shape[2]):
        if c % 20 <6 or i %20 < 6:
          img[c][i][j] = 0
  cv2.imwrite(filepath,img)


if __name__=="__main__":
  pool = multiprocessing.Pool(processes = 32)
  
  for i in range(10000):
    color = int(i/ 40)
    img = np.ones([720,1280,3], np.uint8) * (255-color)
    filename = "w2bpic" + str(i) +".jpg"
    filepath = os.path.join(video_dir, filename)
    cv2.imwrite(filepath,img)

  print("start gen vpic")
  for i in range(10000):
    filename = "vpic" + str(i) +".jpg"
    filepath = os.path.join(video_dir, filename)
    color = 200 + (i % 50 )
    pool.apply_async(vpic,[filepath, color])


  print("start gen hpic")
  for i in range(10000):
    filename = "hpic" + str(i) +".jpg"
    filepath = os.path.join(video_dir, filename)
    color = 200 + (i % 50 )
    pool.apply_async(hpic,[filepath, color])

  print("start gen vhpic")
  for i in range(10000):
    filename = "vhpic" + str(i) +".jpg"
    filepath = os.path.join(video_dir, filename)
    color = 200 + (i % 50 )
    pool.apply_async(vhpic,[filepath, color])

  pool.close()  
  pool.join()

