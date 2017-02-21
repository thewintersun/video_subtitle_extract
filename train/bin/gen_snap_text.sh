#!/bin/bash

#生成一个视频和一个字幕合并之后，每句话的图片和文字对



if [ $# != 7 ];then
   echo $0" video subtitle.ass fontname  marginleft marginv outline shadow"
   exit 0
fi


video=$1
subtitle=$2
fontname=$3
marginleft=$4
marginv=$5
outline=$6
shadow=$7


#随机数，让字幕在一定区域随机变动
random20=$(($RANDOM%20))
random40=$(($RANDOM%40))

marginleft=$((${marginleft}+${random40}))
marginv=$((${marginv}+${random20}))


outputdir="../output_raw_data/"
one_textfile=${outputdir}"/all.txt"
pic_outputdir=${outputdir}"/pic/"
text_outputdir=${outputdir}"/text/"
mkdir -p ${pic_outputdir}
mkdir -p ${text_outputdir}


tempdir="../temp"
mkdir -p $tempdir

video_name_suffix=`echo ${video} | awk -F"." '{print $NF;}'`

temp_video_file=${tempdir}"/temp_embed_video."$video_name_suffix
temp_cut_video_file=${tempdir}"/temp_cut_video."$video_name_suffix

#生成嵌入字幕的视频
echo "embedding "${video}" and "${subtitle}
./embed.sh ${video} ${subtitle} ${fontname}  ${marginleft} ${marginv} ${outline} ${shadow} ${temp_video_file}


x=`echo "scale=4; ${marginleft}  + 50 " | bc`
y=`echo "scale=4; ${marginv} * 1.88 - 2 " | bc` #对于y分辨率是540的


#cut视频
./cut_video.sh ${temp_video_file} 720 30 $x $y ${temp_cut_video_file}



# 根据字幕时间截屏
subtitle_name_prefix=`echo ${subtitle} | awk -F"/" '{print $NF}' | awk -F"." '{print $1;}'`
video_name_prefix=`echo ${video} | awk -F"/" '{print $NF}' | awk -F"." '{print $1;}'`
while read line
do
  col1=`echo $line | awk '{print $1;}'`
  if [ "$col1" == "Dialogue:" ]; then
    start_time=`echo $line | awk -F"," '{print $2;}'`
    text=`echo $line | awk -F"," '{print $NF;}'`
    time_str=${start_time//:/.}

    pic_filename=${video_name_prefix}_${subtitle_name_prefix}_${fontname}_${marginleft}_${marginv}_${outline}_${shadow}"_"${time_str}".jpg"
    pic_outputfile=${pic_outputdir}${pic_filename}

    text_filename_prefix=${video_name_prefix}_${subtitle_name_prefix}_${fontname}_${marginleft}_${marginv}_${outline}_${shadow}"_"${time_str}
    text_filename=${text_filename_prefix}".txt"
    text_outputfile=${text_outputdir}${text_filename}

    ./snapshot.sh ${temp_cut_video_file} ${start_time} ${pic_outputfile}
    
    echo ${text_filename_prefix} ${text} > ${text_outputfile}
    echo ${text_filename_prefix} ${text} >> ${one_textfile}
  fi
done < ${subtitle}

rm -rf ${temp_video_file}
rm -rf ${temp_cut_video_file}





