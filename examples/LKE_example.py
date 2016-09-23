# for local run, before pygraphc packaging
import sys
sys.path.insert(0, '../pygraphc/misc')
from LKE import *

RawLogPath = '/home/hudan/Git/labeled-authlog/dataset/161.166.232.17'
RawLogFile = 'auth.log.anon'
OutputPath = './results'
para = Para(path=RawLogPath, logname=RawLogFile, save_path=OutputPath)

myparser = LKE(para)
time = myparser.main_process()

print ('The running time of LKE is', time)
