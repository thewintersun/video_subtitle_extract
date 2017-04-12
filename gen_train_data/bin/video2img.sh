#!/bin/bash

videofile_list="./videofile_list"

#找出来一个文件夹下的所有嵌套的所有文件
function ergodic(){  
        for file in ` ls $1 `  
        do  
                if [ -d $1"/"$file ]  
                then  
                        ergodic $1"/"$file  
                else  
                        echo $1"/"$file >> $videofile_list
                fi  
        done  
}  

>$videofile_list

outputdir="../videopic"

mkdir -p $outputdir

#一秒钟截几张图
img_number_per_sencond=0.5

#另外一个目录的视频
video_dir="../../ftpvideo/"
ergodic $video_dir

while read line
do
  video=$line
  echo $video

  v_array=(${video//// })
  num=${#v_array[@]}
  video_name=${v_array[$num-1]}

  video_name_array=(${video_name//./ })
  num=${#video_name_array[@]}

  video_prefix=${video_name_array[$num-2]}

  ffmpeg -i $video -r $img_number_per_sencond -f image2 ${outputdir}/${video_prefix}"-v-"%6d.jpg

done < $videofile_list

video_dir="../../download/video/"
for v in `ls $video_dir*mkv`;
do
  video=$video_dir/$v
  echo $video
  
  v_array=(${v//// })
  num=${#v_array[@]}
  video_name=${v_array[$num-1]}

  video_name_array=(${video_name//./ })
  num=${#video_name_array[@]}

  video_prefix=${video_name_array[$num-2]}

  ffmpeg -i $video -r $img_number_per_sencond -f image2 ${outputdir}/${video_prefix}"-"%6d.jpg

done

