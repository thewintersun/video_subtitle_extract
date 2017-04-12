#!/bin/bash

rm -rf ../videopic

mkdir ../videopic

./video2img.sh

python main_gen_change_picvalue.py

python main_gen_other_backgroud_pic.py

python main_gen_pic.py

./shuffle_file.sh ../data/record/pic_and_text.record > ../data/record/pic_and_text.record.shuffle

python split_traindata_to_8_part.py

python main_gen_tfrecord.py 
