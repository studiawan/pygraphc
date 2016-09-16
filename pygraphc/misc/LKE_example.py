from LKE import *

RawLogPath = './'
RawLogFile = 'rawlog.log'
OutputPath = './results/'
para=Para(path=RawLogPath, logname=RawLogFile, savePath=OutputPath)

myparser = LKE(para)
time=myparser.mainProcess()

print ('The running time of LKE is', time)
