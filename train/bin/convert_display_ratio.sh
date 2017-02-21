#!/bin/bash


video_dir="../video"

for v in `ls ${video_dir}`
do
  video_file=${video_dir}/$v
  display_ratio=`ffmpeg -i $video_file 2>&1 | grep Stream | grep Video | awk -F"[" '{print $1}'| awk '{print $NF}'`
  display_bili=`ffmpeg -i $video_file 2>&1 | grep Stream | grep Video | awk -F"]" '{print $1}'|awk '{print $NF;}'`
  if [ "${display_bili}" != "16:9" ];then
    echo "file "${video_file}" not match 16:9, it bili is "${display_bili}
    continue
  fi

  if [ "$display_ratio" == "960x540" ];then
    echo "file "${video_file}" is already 960x540"
    continue
  fi

  outputfile=${video_dir}"/convert_"$v
  echo "convert file "${video_file}" to 960x540"
  ffmpeg -i ${video_file} -s 960x540 ${outputfile}
done
