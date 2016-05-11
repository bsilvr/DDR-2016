import simpy
import numpy as np
from scipy.misc import factorial

class NodeStats:
    """
    Node stats recording
    bw: Link bandwidth
    """
    def __init__(self,bw):
        self.vcs_total=0
        self.vcs_acc=0
        self.vcs_blk=0
        self.bw=bw
        self.available_bw=bw
        self.lastloadchange=0
        self.loadint=0

def vc_generator(env,av_rate,av_duration,b,stats):
    """
    VC generator
    env: SimPy environment
    av_rate: Average VC requests rate
    av_duration: Average VC duration
    b: VC required bandwidth
    stats: Node stats recording (NodeStats class)
    """
    while True:
        yield env.timeout(np.random.exponential(1.0/av_rate))
        stats.vcs_total += 1
        if stats.available_bw>=b:
            stats.vcs_acc += 1
            stats.loadint += (1.0/stats.bw)*(stats.bw-stats.available_bw)*(env.now-stats.lastloadchange)
            stats.lastloadchange=env.now
            stats.available_bw -= b
            print("time %f: VC %d started"%(env.now,stats.vcs_total))
            env.process(vc(env,stats.vcs_total,av_duration,b,stats))
        else:
            stats.vcs_blk += 1
            print("time %f: VC %d blocked"%(env.now,stats.vcs_total))

def vc(env,id,av_duration,b,stats):
    """
    VC object
    env: SimPy environment
    id: VC identifier
    av_duration: Average VC duration
    b: VC required bandwidth
    stats: Global stats recording (NodeStats class)
    """
    yield env.timeout(np.random.exponential(av_duration))
    stats.loadint += (1.0/stats.bw)*(stats.bw-stats.available_bw)*(env.now-stats.lastloadchange)
    stats.lastloadchange=env.now
    stats.available_bw += b
    print("time %f: VC %d ended"%(env.now,id))

lamb=3
invmu=2
b=2
B=32
C=B/b
simtime=3000

l_norm = [1,2,3,4,5]
l_spec = [1,1.5,2,2.5,3]
m = [2,4,6,8,10]
bs = [16,24,32]
R = [0,4,8,16]

res_pb = []
res_ll = []
the_pb = []
the_ll = []


stats_norm=NodeStats(bs[0]-R[0])
stats_spec=NodeStats(bs[0])

env = simpy.Environment()

env.process(vc_generator(env,l_norm[4],m[0],2,stats_norm))
env.process(vc_generator(env,l_spec[4],m[0],4,stats_spec))
env.run(simtime)


sim_pb_norm = 1.0*stats_norm.vcs_blk/stats_norm.vcs_total
sim_ll_norm = 100.0*stats_norm.loadint/simtime

sim_pb_spec = 1.0*stats_spec.vcs_blk/stats_spec.vcs_total
sim_ll_spec = 100.0*stats_spec.loadint/simtime

print
print("Simulated Normal Block Probability=%f"%(sim_pb_norm))
print("Simulated Normal Average Link Load=%.2f%%"%(sim_ll_norm))
print
print("Simulated Special Block Probability=%f"%(sim_pb_spec))
print("Simulated Special Average Link Load=%.2f%%"%(sim_ll_spec))
print
print "link load: " + str((stats_norm.loadint+stats_spec.loadint)/simtime)




