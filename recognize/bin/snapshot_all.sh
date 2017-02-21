#!/bin/bash


if [ $# != 2 ];then
   echo $0" video  outputdir"
   exit 0
fi

video=$1
outputdir=$2
record_file="../record/snapshot.record"

function get_video_time {
  v=$1
  time=`ffmpeg -i $v 2>&1| grep Duration | awk '{print substr($2,0,length($2)-4); }' | awk '{split($1,a,":"); print ((a[1] * 60)+a[2])*60 + a[3];}'`
  echo $time
}

>$record_file

total_time=`get_video_time $video`
total_time=$(($total_time-10))
start_time=10
while [ `expr $start_time \< $total_time` == 1 ]
do
  second=`echo $start_time % 60 | bc`
  minall=`echo $start_time / 60 | bc`
  min=`echo $minall % 60 | bc`
  hour=`echo $minall / 60 | bc`
  second=$(printf '%02d' $second)
  min=$(printf '%02d' $min)
  hour=$(printf '%02d' $hour)

  snap_time=$hour":"$min":"$second".00"
  ffmpeg -ss ${snap_time} -i ${video} -y ${outputdir}/$start_time".00.jpg"
  echo $video" "$start_time".00 "${outputdir}/$start_time".00.jpg" >> $record_file

  snap_time2=$hour":"$min":"$second".50"
  ffmpeg -ss ${snap_time2} -i ${video} -y ${outputdir}/$start_time".50.jpg"
  echo $video" "$start_time".50 "${outputdir}/$start_time".50.jpg" >> $record_file
  
  start_time=`echo $start_time + 1 | bc`
done
