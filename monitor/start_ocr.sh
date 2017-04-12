#!/bin/bash


result=`ps axu | grep main_ocr.py|wc -l`
if [ $result -gt 1 ]; then
  echo "already at ocr exit."
  exit 1
fi

#没有下载，则启动下载
projectdir="/disk2/code/git/video_subtitle_extract/"
ocr_dir=${projectdir}"/ocr/bin/"

cd $ocr_dir

nohup python main_ocr.py &

