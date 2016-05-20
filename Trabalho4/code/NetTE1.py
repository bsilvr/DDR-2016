import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from mygeo import getgeo, geodist
import itertools
import random
import pickle
import argparse

mu=1e9/8000 #link speed in pkts/sec
lightspeed=300000.0 #Km/sec

def listStats(L):
	#Returns the mean and maximum values of a list of numbers with generic keys
	#	returns also the key of the maximum value
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

with open(filename) as f:
	nodes, links, pos, tm = pickle.load(f)

print(tm)

net=nx.DiGraph()
for node in nodes:
	net.add_node(node)

for link in links:
	dist=geodist((pos[link[0]][1],pos[link[0]][0]),(pos[link[1]][1],pos[link[1]][0]))
	net.add_edge(link[0],link[1],distance=dist, load=0, delay=0)
	net.add_edge(link[1],link[0],distance=dist, load=0, delay=0)
	print(link,dist,(pos[link[0]][1],pos[link[0]][0]),(pos[link[1]][1],pos[link[1]][0]))

nx.draw(net,pos,with_labels=True)
plt.show()

allpairs=list(itertools.permutations(nodes,2))
sol={}

for pair in allpairs:
	path=nx.shortest_path(net,pair[0],pair[1],weight='distance')
	sol.update({pair:path})
	for i in range(0,len(path)-1):
		net[path[i]][path[i+1]]['load']+=tm[pair[0]][pair[1]]

print('---')
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
for i in link_load:
	if link_load[i] > m_value:
		m_flow = i
		m_value = link_load[i]

print "Worst link load on link %s with load of: %.2f%%" % (m_flow, m_value)


print('---')
m_flow = ""
m_value = 0
for i in one_way_times:
	if one_way_times[i] > m_value:
		m_flow = i
		m_value = one_way_times[i]

print "Worst one way time on link %s with delay of: %.2f micro sec" % (m_flow, m_value)

print('---')
m_flow = ""
m_value = 0
for i in flow_delay:
	if flow_delay[i] > m_value:
		m_flow = i
		m_value = flow_delay[i]

print "Worst QoS on flow %s with delay of: %.2f micro sec" % (m_flow, m_value)





