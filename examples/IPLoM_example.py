# for local run, before pygraphc packaging
import sys
sys.path.insert(0, '../pygraphc/misc')
from IPLoM import *
sys.path.insert(0, '../pygraphc/clustering')
from ClusterUtility import *
from ClusterEvaluation import *

# set path
ip_address = '161.166.232.17'
standard_path = '/home/hudan/Git/labeled-authlog/dataset/' + ip_address
standard_file = standard_path + 'auth.log.anon.labeled'
analyzed_file = 'auth.log.anon'
prediction_file = 'iplom-result-' + ip_address + '.txt'
OutputPath = './results'
para = Para(path=standard_path, logname=analyzed_file, save_path=OutputPath)

# call IPLoM and get clusters
myparser = IPLoM(para)
time = myparser.main_process()
clusters = myparser.get_clusters()
original_logs = myparser.get_logs()

# set cluster label to get evaluation metrics
ClusterUtility.set_cluster_label_id(None, clusters, original_logs, prediction_file)
homogeneity_completeness_vmeasure = ClusterEvaluation.get_homogeneity_completeness_vmeasure(standard_file,
                                                                                            prediction_file)

print homogeneity_completeness_vmeasure
print ('The running time of IPLoM is', time)
