#!/bin/bash


if [ $# != 3 ];then
   echo $0" video time outputfile"
   exit 0
fi

video=$1
time=$2
outputfile=$3

ffmpeg -ss ${time} -i ${video} -y ${outputfile}
