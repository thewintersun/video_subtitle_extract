#!/bin/bash


result=`ps axu | grep download_multi.py|wc -l`
if [ $result -gt 1 ]; then
  echo "already at downloading exit."
  exit 1
fi

#没有下载，则启动下载
projectdir="/disk2/code/git/video_subtitle_extract/"
download_dir=${projectdir}"/download"

cd $download_dir

nohup python download_multi.py &

