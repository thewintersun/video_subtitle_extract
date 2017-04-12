#!/bin/bash


if [ $# != 4 ];then
   echo $0" video  outputdir picfile_prefix record_file"
   exit 0
fi

video=$1
outputdir=$2
picfile_prefix=$3
record_file=$4

function get_video_time {
  v=$1
  time=`ffmpeg -i $v 2>&1| grep Duration | awk '{print substr($2,0,length($2)-4); }' | awk '{split($1,a,":"); print ((a[1] * 60)+a[2])*60 + a[3];}'`
  echo $time
}

mkdir -p $outputdir
mkdir -p ../record

>$record_file

total_time=`get_video_time $video`

start_time=0

ffmpeg -i $video -r 10 -f image2 ${outputdir}/${picfile_prefix}"-"%6d.jpg

#从第二个开始，因为jpg是从1开始的，并且第一个图片不要
i_jpg=2

while [ `expr $start_time \< $total_time` == 1 ]
do
  i_jpg_str=$(printf '%06d' $i_jpg)
  echo $video" "${start_time}".00 "${outputdir}/${picfile_prefix}"-"${i_jpg_str}.jpg >> $record_file

  i_jpg=`echo $i_jpg + 1 | bc`
  i_jpg_str=$(printf '%06d' $i_jpg)
  echo $video" "${start_time}".10 "${outputdir}/${picfile_prefix}"-"${i_jpg_str}.jpg >> $record_file
  
  i_jpg=`echo $i_jpg + 1 | bc`
  i_jpg_str=$(printf '%06d' $i_jpg)
  echo $video" "${start_time}".20 "${outputdir}/${picfile_prefix}"-"${i_jpg_str}.jpg >> $record_file
  
  i_jpg=`echo $i_jpg + 1 | bc`
  i_jpg_str=$(printf '%06d' $i_jpg)
  echo $video" "${start_time}".30 "${outputdir}/${picfile_prefix}"-"${i_jpg_str}.jpg >> $record_file

  i_jpg=`echo $i_jpg + 1 | bc`
  i_jpg_str=$(printf '%06d' $i_jpg)
  echo $video" "${start_time}".40 "${outputdir}/${picfile_prefix}"-"${i_jpg_str}.jpg >> $record_file
  
  i_jpg=`echo $i_jpg + 1 | bc`
  i_jpg_str=$(printf '%06d' $i_jpg)
  echo $video" "${start_time}".50 "${outputdir}/${picfile_prefix}"-"${i_jpg_str}.jpg >> $record_file
  
  i_jpg=`echo $i_jpg + 1 | bc`
  i_jpg_str=$(printf '%06d' $i_jpg)
  echo $video" "${start_time}".60 "${outputdir}/${picfile_prefix}"-"${i_jpg_str}.jpg >> $record_file

  i_jpg=`echo $i_jpg + 1 | bc`
  i_jpg_str=$(printf '%06d' $i_jpg)
  echo $video" "${start_time}".70 "${outputdir}/${picfile_prefix}"-"${i_jpg_str}.jpg >> $record_file
  
  i_jpg=`echo $i_jpg + 1 | bc`
  i_jpg_str=$(printf '%06d' $i_jpg)
  echo $video" "${start_time}".80 "${outputdir}/${picfile_prefix}"-"${i_jpg_str}.jpg >> $record_file
  
  i_jpg=`echo $i_jpg + 1 | bc`
  i_jpg_str=$(printf '%06d' $i_jpg)
  echo $video" "${start_time}".90 "${outputdir}/${picfile_prefix}"-"${i_jpg_str}.jpg >> $record_file
  
  start_time=`echo $start_time + 1 | bc`
 
  i_jpg=`echo $i_jpg + 1 | bc`

done
exit 0

