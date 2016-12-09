from pygraphc.misc.IPLoM import *
from pygraphc.evaluation.ExternalEvaluation import *

# set input path
dataset_path = '/home/hudan/Git/labeled-authlog/dataset/Hofstede2014/dataset1_perday/'
groundtruth_file = dataset_path + 'Dec 1.log.labeled'
analyzed_file = 'Dec 1.log'
OutputPath = '/home/hudan/Git/pygraphc/result/misc/'
prediction_file = OutputPath + 'Dec 1.log.perline'
para = Para(path=dataset_path, logname=analyzed_file, save_path=OutputPath)

# call IPLoM and get clusters
myparser = IPLoM(para)
time = myparser.main_process()
clusters = myparser.get_clusters()
original_logs = myparser.logs

# set cluster label to get evaluation metrics
ExternalEvaluation.set_cluster_label_id(None, clusters, original_logs, prediction_file)

# get evaluation of clustering performance
ar = ExternalEvaluation.get_adjusted_rand(groundtruth_file, prediction_file)
ami = ExternalEvaluation.get_adjusted_mutual_info(groundtruth_file, prediction_file)
nmi = ExternalEvaluation.get_normalized_mutual_info(groundtruth_file, prediction_file)
h = ExternalEvaluation.get_homogeneity(groundtruth_file, prediction_file)
c = ExternalEvaluation.get_completeness(groundtruth_file, prediction_file)
v = ExternalEvaluation.get_vmeasure(groundtruth_file, prediction_file)

# print evaluation result
print ar, ami, nmi, h, c, v
print ('The running time of IPLoM is', time)
