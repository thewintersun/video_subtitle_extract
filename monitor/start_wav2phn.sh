#!/bin/bash


result=`ps axu | grep main_wav2phn.py|wc -l`
if [ $result -gt 1 ]; then
  echo "already at main_wav2phn exit."
  exit 1
fi

#没有下载，则启动下载
projectdir="/disk2/code/git/video_subtitle_extract/"
wav2phn_dir=${projectdir}"/wav2phn/"

cd $wav2phn_dir

nohup python main_wav2phn.py &

