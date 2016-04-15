import simpy
import numpy as np
import matplotlib.pyplot as plt
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

l = [1,1.5,2,2.5,3]
m = [2,4,6,8,10]
bs = [16,24,32]

res_pb = []
res_ll = []
the_pb = []
the_ll = []

###################################################################################################################

# for j in l:
#     stats=NodeStats(B)
#     env = simpy.Environment()
#     env.process(vc_generator(env,j,invmu,b,stats))
#     env.run(simtime)
#     sim_pb = 1.0*stats.vcs_blk/stats.vcs_total
#     sim_ll = 100.0*stats.loadint/simtime
#     print("Simulated Block Probability=%f"%(sim_pb))
#     print("Simulated Average Link Load=%.2f%%"%(sim_ll))
#     rho=j*invmu
#     i=np.arange(0,C+1)
#     blkp=(np.power(1.0*rho,C)/factorial(C))/np.sum(np.power(1.0*rho,i)/factorial(i))
#     print("Theoretical Block Probability=%f"%(blkp))
#     i1=np.arange(1,C+1)
#     linkload=(1.0/C)*np.sum(np.power(1.0*rho,i1)/factorial(i1-1))/np.sum(np.power(1.0*rho,i)/factorial(i))
#     print("Theoretical Average Link Load=%.2f%%"%(100*linkload))
#     res_pb.append(sim_pb)
#     res_ll.append(sim_ll)
#     the_pb.append(blkp)
#     the_ll.append(100*linkload)


# fig, ax1 = plt.subplots()
# line1, = ax1.plot(l, res_pb, 'b')
# line2, = ax1.plot(l, the_pb, 'b--')
# ax1.set_xlabel('Requests per Minute')
# # Make the y-axis label and tick labels match the line color.
# ax1.set_ylabel('Blocking Probability', color='b')
# for tl in ax1.get_yticklabels():
#     tl.set_color('b')

# ax2 = ax1.twinx()

# ax2.plot(l, res_ll, 'r')
# ax2.plot(l, the_ll, 'r--')
# ax2.set_ylabel('Link Capacity %', color='r')
# for tl in ax2.get_yticklabels():
#     tl.set_color('r')

# plt.legend([line1, line2], ["Simulated", "Theoretical"], loc=2)

# ax = plt.gca()
# legend = ax.get_legend()
# legend.legendHandles[0].set_color('black')
# legend.legendHandles[1].set_color('black')

# plt.show()

# ##########################################################################################

# res_pb = []
# res_ll = []
# the_pb = []
# the_ll = []

# for j in m:
#     stats=NodeStats(B)
#     env = simpy.Environment()
#     env.process(vc_generator(env,lamb,j,b,stats))
#     env.run(simtime)
#     sim_pb = 1.0*stats.vcs_blk/stats.vcs_total
#     sim_ll = 100.0*stats.loadint/simtime
#     print("Simulated Block Probability=%f"%(sim_pb))
#     print("Simulated Average Link Load=%.2f%%"%(sim_ll))
#     rho=lamb*j
#     i=np.arange(0,C+1)
#     blkp=(np.power(1.0*rho,C)/factorial(C))/np.sum(np.power(1.0*rho,i)/factorial(i))
#     print("Theoretical Block Probability=%f"%(blkp))
#     i1=np.arange(1,C+1)
#     linkload=(1.0/C)*np.sum(np.power(1.0*rho,i1)/factorial(i1-1))/np.sum(np.power(1.0*rho,i)/factorial(i))
#     print("Theoretical Average Link Load=%.2f%%"%(100*linkload))
#     res_pb.append(sim_pb)
#     res_ll.append(sim_ll)
#     the_pb.append(blkp)
#     the_ll.append(100*linkload)

# fig, ax1 = plt.subplots()
# line1, = ax1.plot(m, res_pb, 'b')
# line2, = ax1.plot(m, the_pb, 'b--')
# ax1.set_xlabel('Duration of Requests')
# # Make the y-axis label and tick labels match the line color.
# ax1.set_ylabel('Blocking Probability', color='b')
# for tl in ax1.get_yticklabels():
#     tl.set_color('b')

# ax2 = ax1.twinx()

# ax2.plot(m, res_ll, 'r')
# ax2.plot(m, the_ll, 'r--')
# ax2.set_ylabel('Link Capacity %', color='r')
# for tl in ax2.get_yticklabels():
#     tl.set_color('r')

# plt.legend([line1, line2], ["Simulated", "Theoretical"], loc=2)

# ax = plt.gca()
# legend = ax.get_legend()
# legend.legendHandles[0].set_color('black')
# legend.legendHandles[1].set_color('black')

# plt.show()

##########################################################################################

res_pb = []
res_ll = []
the_pb = []
the_ll = []

for j in bs:
    C = j/b
    stats=NodeStats(j)
    env = simpy.Environment()
    env.process(vc_generator(env,lamb,invmu,b,stats))
    env.run(simtime)
    sim_pb = 1.0*stats.vcs_blk/stats.vcs_total
    sim_ll = 100.0*stats.loadint/simtime
    print("Simulated Block Probability=%f"%(sim_pb))
    print("Simulated Average Link Load=%.2f%%"%(sim_ll))
    rho=lamb*invmu
    i=np.arange(0,C+1)
    blkp=(np.power(1.0*rho,C)/factorial(C))/np.sum(np.power(1.0*rho,i)/factorial(i))
    print("Theoretical Block Probability=%f"%(blkp))
    i1=np.arange(1,C+1)
    linkload=(1.0/C)*np.sum(np.power(1.0*rho,i1)/factorial(i1-1))/np.sum(np.power(1.0*rho,i)/factorial(i))
    print("Theoretical Average Link Load=%.2f%%"%(100*linkload))
    res_pb.append(sim_pb)
    res_ll.append(sim_ll)
    the_pb.append(blkp)
    the_ll.append(100*linkload)

fig, ax1 = plt.subplots()
line1, = ax1.plot(bs, res_pb, 'b')
line2, = ax1.plot(bs, the_pb, 'b--')
ax1.set_xlabel('BandWitdh')
# Make the y-axis label and tick labels match the line color.
ax1.set_ylabel('Blocking Probability', color='b')
for tl in ax1.get_yticklabels():
    tl.set_color('b')

ax2 = ax1.twinx()

ax2.plot(bs, res_ll, 'r')
ax2.plot(bs, the_ll, 'r--')
ax2.set_ylabel('Link Capacity %', color='r')
for tl in ax2.get_yticklabels():
    tl.set_color('r')

plt.legend([line1, line2], ["Simulated", "Theoretical"], loc=1)

ax = plt.gca()
legend = ax.get_legend()
legend.legendHandles[0].set_color('black')
legend.legendHandles[1].set_color('black')

plt.show()
