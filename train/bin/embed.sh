#!/bin/bash


if [ $# != 8 ];then
   echo $0" video subtitle.ass fontname  marginleft marginv outline shadow outputfile"
   exit 0
fi

video=$1
subtitle=$2
fontname=$3
marginleft=$4
marginv=$5
outline=$6
shadow=$7
outputfile=$8

ffmpeg -y -i $video -vf subtitles="f=${subtitle}:force_style='FontName=${fontname},Alignment=4,MarginL=${marginleft},MarginV=${marginv},Fontsize=14,Outline=${outline},Shadow=${shadow}'" ${outputfile}

exit 0
