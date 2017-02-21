
import shuffle_data

output_feature_path="./output/allimg2.cvs"
output_label_path="./output/alllabel2"

if 1==1:
    shuffle_data.shuffle_file(output_feature_path, output_feature_path + ".1")
    shuffle_data.shuffle_file(output_label_path, output_label_path + ".1")

    # shuffle 2nd
    shuffle_data.shuffle_file(output_feature_path + ".1",
                              output_feature_path + ".2")
    shuffle_data.shuffle_file(output_label_path + ".1",
                              output_label_path + ".2")

    # shuffle 3nd
    shuffle_data.shuffle_file(output_feature_path + ".2",
                              output_feature_path + ".3")
    shuffle_data.shuffle_file(output_label_path + ".2",
                              output_label_path + ".3")

    # shuffle 4nd
    shuffle_data.shuffle_file(output_feature_path + ".3",
                              output_feature_path + ".4")
    shuffle_data.shuffle_file(output_label_path + ".3",
                              output_label_path + ".4")
