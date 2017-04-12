#!/bin/bash


if [ $# != 2 ];then
  echo $0 video outputwav
  exit 0
fi

video=$1
outputwav=$2

ffmpeg -y -i $video -ab 16000 -ar 16000  $outputwav
exit $?
