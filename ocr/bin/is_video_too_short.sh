#!/bin/bash

if [ $# != 2 ];then
   echo $0" video mintime"
   exit 0
fi

video=$1
mintime=$2

function get_video_time {
  v=$1
  time=`ffmpeg -i $v 2>&1| grep Duration | awk '{print substr($2,0,length($2)-4); }' | awk '{split($1,a,":"); print ((a[1] * 60)+a[2])*60 + a[3];}'`
  echo $time
}


total_time=`get_video_time $video`

if [ `expr $total_time \< $mintime` == 1 ];then
  exit 1
fi
exit 0

