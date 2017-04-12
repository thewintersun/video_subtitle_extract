#生成语言模型

先安装srilm, 把安装的ngram文件放到ocr/bin下面

然后用命令生成语言模型：

  - ngram-count -text textfile -order 3 -lm chinese.lm3

textfile文件中的汉字必须以空格分开


