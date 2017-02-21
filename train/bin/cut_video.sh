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

ffmpeg -y -i $video -vf crop=${width}:${height}:$x:$y $outputfile
