#!/bin/bash

if [ $# != 1 ];then
   echo $0" video"
   exit 0
fi

video=$1

function get_video_width {
  v=$1
  width=`ffmpeg -i $v 2>&1| grep Stream | grep Video | awk '{
      split($0,x_split_array, "x");
      split(x_split_array[1], empty_split_array, " ");
      width = empty_split_array[length(empty_split_array)];
      if(width <100){
        split(x_split_array[2], empty_split_array, " ");
        width = empty_split_array[length(empty_split_array)];
      }
      print width; }'`
  echo $width
}


width=`get_video_width $video`
echo $width



