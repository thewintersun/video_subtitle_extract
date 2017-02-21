#!/bin/bash


if [ $# != 2 ];then
  echo $0 url  outputfilename
  exit 0
fi


url=$1
outputfilename=$2

format="--format=HD"

iqiyi_grep=`echo $url | grep "iqiyi.com"`
youku_grep=`echo $url | grep "youku.com"`

if [ "$iqiyi_grep" != "" ];then
  format="--format=HD"
fi

if [ "$youku_grep" != "" ];then
  format="--format=mp4"
fi

you-get $format -o "../video/" -O $outputfilename $url 2>>../log/youget.log

