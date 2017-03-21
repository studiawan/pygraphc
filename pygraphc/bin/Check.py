import csv
from os import listdir
from pygraphc.evaluation.ExternalEvaluation import ExternalEvaluation

# read result and ground truth
result_dir = '/home/hudan/Git/pygraphc/result/improved_majorclust/Kippo/per_day/'
groundtruth_dir = '/home/hudan/Git/labeled-authlog/dataset/Kippo/attack/'
result_files = listdir(result_dir)

# open evaluation file
f = open('check.csv', 'wt')
writer = csv.writer(f)

# set header
header = ('file_name', 'tp', 'fp', 'fn', 'tn', 'specificity', 'precision', 'recall', 'accuracy')
writer.writerow(header)

for result_file in result_files:
    if result_file.endswith('.anomaly.perline.txt'):
        filename = result_file.split('.anomaly')[0]
        print filename
        groundtruth_file = groundtruth_dir + filename + '.attack'

        # check confusion matrix
        true_false, specificity, precision, recall, accuracy = \
            ExternalEvaluation.get_confusion(groundtruth_file, result_dir + result_file)

        # write evaluation result to file
        row = (filename, true_false[0], true_false[1], true_false[2], true_false[3],
               specificity, precision, recall, accuracy)
        writer.writerow(row)

f.close()
