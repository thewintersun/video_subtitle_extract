#!/bin/bash


if [ $# != 3 ];then
  echo $0 url output_dir outputfilename
  exit 0
fi


url=$1
output_dir=$2
outputfilename=$3

format="--format=HD"

iqiyi_grep=`echo $url | grep "iqiyi.com"`
youku_grep=`echo $url | grep "youku.com"`

if [ "$iqiyi_grep" != "" ];then
  #format="--format=HD"
  format=""
fi

if [ "$youku_grep" != "" ];then
  format="--format=mp4"
fi

mkdir -p  ./log
you-get $format -o ${output_dir} -O ${outputfilename}.mp4 $url 2>>./log/youget.log
if [ $? != 0 ];then
  echo "you-get error "$url
  exit 1
fi

#ffmpeg -i ${output_dir}/${outputfilename}.mp4 -vcodec copy -acodec copy ${output_dir}/$outputfilename.mkv

#rm ${output_dir}/${outputfilename}.mp4
exit 0
