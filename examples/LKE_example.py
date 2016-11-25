from pygraphc.misc.LKE import *
from pygraphc.evaluation.ExternalEvaluation import *

# set input and output path
ip_address = '161.166.232.17'
standard_path = '/home/hudan/Git/labeled-authlog/dataset/Hofstede2014/dataset1/' + ip_address
standard_file = standard_path + 'auth.log.anon.labeled'
analyzed_file = 'auth.log.anon'
prediction_file = 'lke-result-' + ip_address + '.txt'
OutputPath = './results'
para = Para(path=standard_path, logname=analyzed_file, save_path=OutputPath)

# run LKE method
myparser = LKE(para)
time = myparser.main_process()
clusters = myparser.get_clusters()
original_logs = myparser.logs

# perform evaluation
ExternalEvaluation.set_cluster_label_id(None, clusters, original_logs, prediction_file)
homogeneity_completeness_vmeasure = ExternalEvaluation.get_homogeneity_completeness_vmeasure(standard_file,
                                                                                             prediction_file)
# print evaluation result
print homogeneity_completeness_vmeasure
print ('The running time of LKE is', time)
