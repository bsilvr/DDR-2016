import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from mygeo import getgeo, geodist
import itertools
import random
import pickle
import argparse
import sys

mu=1e9/8000 #link speed in pkts/sec
lightspeed=300000.0 #Km/sec


class Logger(object):
    def __init__(self, fname):
        self.terminal = sys.stdout
        self.log = open(fname, "w+")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def close(self):
        self.log.close()


def GreedyRandomized(allpairs, net, tm):
    random.shuffle(allpairs)
    sol={}
    for pair in allpairs:
        path=nx.shortest_path(net,pair[0],pair[1],weight='load')
        sol.update({pair:path})
        for i in range(0,len(path)-1):
            net[path[i]][path[i+1]]['load']+=tm[pair[0]][pair[1]]
            net[path[i]][path[i+1]]['delay']+= 1000000.0/(mu-tm[pair[0]][pair[1]])


    delay_sum = 0
    for link in links:
        delay_sum += 1000000.0/(mu-net[link[0]][link[1]]['load'])

    delay_avg = delay_sum / len(links)

    return sol, delay_avg

def neighbor_solution(pair, net, sol, tm):
    path = sol[pair]
    for i in range(0,len(path)-1):
            net[path[i]][path[i+1]]['load']-=tm[pair[0]][pair[1]]
            net[path[i]][path[i+1]]['delay']-= 1000000.0/(mu-tm[pair[0]][pair[1]])

    path=nx.shortest_path(net,pair[0],pair[1],weight='load')
    sol.update({pair:path})
    for i in range(0,len(path)-1):
        net[path[i]][path[i+1]]['load']+=tm[pair[0]][pair[1]]
        net[path[i]][path[i+1]]['delay']+= 1000000.0/(mu-tm[pair[0]][pair[1]])

    delay_sum = 0
    for link in links:
        delay_sum += 1000000.0/(mu-net[link[0]][link[1]]['load'])

    delay_avg = delay_sum / len(links)

    return sol, delay_avg




def listStats(L):
    #Returns the mean and maximum values of a list of numbers with generic keys
    #   returns also the key of the maximum value
    V=L.values()
    K=L.keys()
    meanL=np.mean(V)
    maxL=np.max(V)
    p=np.where(V==M)[0][0]
    maxLK=K[p]
    return meanL, maxL, maxLK


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', nargs='?', help='input network file', default='network.dat')
args=parser.parse_args()

filename=args.file

sys.stdout = Logger("ex13-" + filename.split(".")[0] + ".txt")

with open(filename) as f:
    nodes, links, pos, tm = pickle.load(f)

#print(tm)

best_sol = None
best_net = None
min_delay = 0
best_run = 0

for i in range(0,1):

    net=nx.DiGraph()
    for node in nodes:
        net.add_node(node)

    for link in links:
        dist=geodist((pos[link[0]][1],pos[link[0]][0]),(pos[link[1]][1],pos[link[1]][0]))
        net.add_edge(link[0],link[1],distance=dist, load=0, delay=0)
        net.add_edge(link[1],link[0],distance=dist, load=0, delay=0)
        #print(link,dist,(pos[link[0]][1],pos[link[0]][0]),(pos[link[1]][1],pos[link[1]][0]))

    nx.draw(net,pos,with_labels=True)
    #plt.show()

    allpairs=list(itertools.permutations(nodes,2))

    sol, delay_avg = GreedyRandomized(allpairs, net, tm)

    repeat = True
    while repeat:
        neighbor_best_sol = None
        neighbor_best_net = None
        neighbor_min_delay = 0
        for j in sol:
            n_sol, n_delay_avg = neighbor_solution(j, net, sol, tm)

            if neighbor_best_sol == None:
                neighbor_best_sol = n_sol
                neighbor_best_net = net
                neighbor_min_delay = n_delay_avg
            else:
                if neighbor_min_delay > delay_avg:
                    neighbor_best_sol = n_sol
                    neighbor_best_net = net
                    neighbor_min_delay = n_delay_avg


        if best_sol == None:
            best_sol = neighbor_best_sol
            best_net = neighbor_best_net
            min_delay = neighbor_min_delay
            best = i
        else:
            if neighbor_min_delay < min_delay:
                best_sol = neighbor_best_sol
                best_net = neighbor_best_net
                min_delay = neighbor_min_delay
                best_run = i
            else:
                repeat = False



sol = best_sol
net = best_net
print('---')
print('Best run was on pass %d'%(best_run))
print('Solution:'+str(sol))

print('---')
one_way_times = {}
link_load = {}
for link in links:
    one_way_times[(link[0],link[1])] = 1000000.0/(mu-net[link[0]][link[1]]['load'])
    link_load[(link[0],link[1])] = 100.0* net[link[0]][link[1]]['load']/mu

    print("#link %s-%s: %d pkts/sec -- link-load: %.2f%% -- one_way_delay: %.2f micro sec"%(link[0],link[1],net[link[0]][link[1]]['load'], link_load[(link[0],link[1])], one_way_times[(link[0],link[1])]))


    one_way_times[(link[1],link[0])] = 1000000.0/(mu-net[link[1]][link[0]]['load'])
    link_load[(link[1],link[0])] = 100.0* net[link[1]][link[0]]['load']/mu

    print("#link %s-%s: %d pkts/sec -- link-load: %.2f%% -- one_way_delay: %.2f micro sec"%(link[1],link[0],net[link[1]][link[0]]['load'], link_load[(link[1],link[0])], one_way_times[(link[1],link[0])]))


print('---')
flow_delay = {}
for i in sol:
    delay = 0
    for j in range(0,len(sol[i])-1):
        delay += one_way_times[(sol[i][j],sol[i][j+1])]
    flow_delay[i] = delay
    print "#flow %s: one way delay: %.2f micro sec" % (i, delay)


print('---')
m_flow = ""
m_value = 0
sum_value = 0
for i in link_load:
    sum_value += link_load[i]
    if link_load[i] > m_value:
        m_flow = i
        m_value = link_load[i]

print "Average link load of: %.2f%%" % (sum_value/len(link_load))
print "Worst link load on link %s with load of: %.2f%%" % (m_flow, m_value)


print('---')
m_flow = ""
m_value = 0
sum_value = 0
for i in one_way_times:
    sum_value += one_way_times[i]
    if one_way_times[i] > m_value:
        m_flow = i
        m_value = one_way_times[i]

print "Average one way time delay of: %.2f micro sec" % (sum_value/len(one_way_times))
print "Worst one way time on link %s with delay of: %.2f micro sec" % (m_flow, m_value)

print('---')
m_flow = ""
m_value = 0
for i in flow_delay:
    if flow_delay[i] > m_value:
        m_flow = i
        m_value = flow_delay[i]

print "Worst QoS on flow %s with delay of: %.2f micro sec" % (m_flow, m_value)

