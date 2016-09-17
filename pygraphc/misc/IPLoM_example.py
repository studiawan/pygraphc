from IPLoM import *

RawLogPath = './'
RawLogFile = 'rawlog.log'
OutputPath = './results'
para=Para(path=RawLogPath, logname=RawLogFile, savePath=OutputPath)

myparser=IPLoM(para)
time=myparser.mainProcess()

print ('The running time of IPLoM is', time)
