import numpy as np
import scipy.stats as stats
import scipy.signal as signal
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import time
import sys
import warnings
warnings.filterwarnings('ignore')

def waitforEnter():
    if sys.version_info[0] == 2:
        raw_input("Press ENTER to continue.")
    else:
        input("Press ENTER to continue.")


plt.ion()
# -1- #
data1=np.loadtxt('../dataFiles/youtube')
print data1
#for i in range(0, 39):
plt.figure(1)
plt.plot(data1[:],marker='s',c='blue',label='dataset 0')
plt.show()
waitforEnter()

M=np.mean(data1,axis=0)
Md=np.median(data1,axis=0)
V=np.var(data1,axis=0)
S=stats.skew(data1)
K=stats.kurtosis(data1)
p=range(5,101,1)
Pr=np.percentile(data1,p,axis=0)

print "Media: %s" % str(M)
print "Mediana: %s" % str(Md)
print "STD: %s" % str(V)
print "Skew: %s" % str(S)
print "Kurtosis: %s" % str(K)




waitforEnter()
