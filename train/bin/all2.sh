#!/bin/bash

#处理一个视频的时候，字幕的y坐标的位置变动区域
min_y=130
max_y=230
step_y=30

#处理一个视频的时候，字幕的x坐标的位置变动区域
min_x=150
max_x=250
step_x=50


#字体列表
font_list="simhei YouYuan 微软雅黑 方正粗圆简体 宋体 碳化硅大黑体"
outline_list="0 2"
shadow_list="0 1"

video_dir="../video/"
all_videos="shici.mkv"

subtitle_dir="../output_subtitle/"
subtitle_file_index=0

#所有字幕的个数
subtitle_num=125

#清空all.txt文件
> ../output_raw_data/all.txt

#遍历每个要处理的视频
for v in $all_videos
do
  videofile=${video_dir}/$v
  
  marginleft=min_x
  marginv=min_y

    for((marginleft=$min_x;marginleft<=${max_x};marginleft=marginleft+${step_x}))
    do
      for((marginv=${min_y};marginv<=${max_y};marginv=marginv+${step_y}))
      do
        for fontname in ${font_list}
        do
          for outline in ${outline_list}
          do
            for shadow in ${shadow_list}
            do

              if [ $subtitle_file_index -gt $subtitle_num ];then
                echo "proccess all subtitle over"
                exit 0
              fi
              if [ "$shadow" == "0" -a "$outline" == "0" ]; then
                continue
              fi
              if [ "$shadow" == "1" -a "$outline" == "2" ]; then
                continue
              fi
            
              subtitle_file=${subtitle_dir}"/"${subtitle_file_index}".ass"
              ./gen_snap_text.sh ${videofile} ${subtitle_file} ${fontname}  ${marginleft} ${marginv} ${outline} ${shadow}
              subtitle_file_index=$(expr $subtitle_file_index + 1)
            done
          done
        done
      done

    
    done
  

  
  
done
