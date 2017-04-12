#coding=utf-8

import os
import cv2
import numpy as np
import threading
import time
import multiprocessing
from multiprocessing import Pool, Lock, Value  


def change_value(img_channel, min,max):
  for i in range(img_channel.shape[0]):
    for j in range(img_channel.shape[1]):
      if img_channel[i][j] > min and img_channel[i][j] < max:
        img_channel[i][j] = img_channel[i][j]*1.0 * 55/255 + 200

def run(filepath):
  img = cv2.imread(filepath, -1)
  img_b = img[:, :, 0]
  img_g = img[:, :, 1]
  img_r = img[:, :, 2]

  change_value(img_b, 50, 200)
  change_value(img_g, 50, 200)
  change_value(img_r, 50, 200)

  img[:, :, 0] = img_b.astype(np.uint8)
  img[:, :, 1] = img_g.astype(np.uint8)
  img[:, :, 2] = img_r.astype(np.uint8)

  filepath_splits = filepath.split("/")
  new_name = filepath_splits[-1].split(".")[0] + "_change"
  filepath_splits[-1] = new_name + "." + filepath_splits[-1].split(".")[-1]
  
  write_filepath = "/".join(filepath_splits)
  print(write_filepath)
  cv2.imwrite(write_filepath, img)

  
current_thread_number = 0

class WorkThread(threading.Thread):
  def __init__(self, filepath):
    threading.Thread.__init__(self)
    self.filepath = filepath

  def run(self):
    global current_thread_number
    img = cv2.imread(self.filepath, -1)
    img_b = img[:, :, 0]
    img_g = img[:, :, 1]
    img_r = img[:, :, 2]

    change_value(img_b, 50, 200)
    change_value(img_g, 50, 200)
    change_value(img_r, 50, 200)

    img[:, :, 0] = img_b.astype(np.uint8)
    img[:, :, 1] = img_g.astype(np.uint8)
    img[:, :, 2] = img_r.astype(np.uint8)

    print(self.filepath)
    cv2.imwrite(self.filepath, img)
    current_thread_number -= 1


if __name__ == "__main__":

  videopic_dir="../videopic/"

  i = 0
  max_number = 80000

  pool = multiprocessing.Pool(processes = 24)   
  
  for f in os.listdir(videopic_dir):
    i += 1
    if i > max_number:
      break

    filepath = os.path.join(videopic_dir, f)
    #print(filepath)
    pool.apply_async(run,[filepath])  

    
  pool.close()  
  pool.join()  
    
