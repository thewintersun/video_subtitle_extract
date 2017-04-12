#!/bin/bash


if [ $# != 6 ];then
   echo $0" video width height x y outputfile"
   exit 0
fi

video=$1
width=$2
height=$3
x=$4
y=$5
outputfile=$6

video_width=`./get_video_width.sh $video`

if [ `expr $video_width \< $width + $x` == 1 ];then
  echo "video with is too short , cut to be short too!"
  width=`expr $video_width - $x`
  
fi

ffmpeg -y -i $video -r 10 -vf crop=${width}:${height}:$x:$y $outputfile
exit $?

