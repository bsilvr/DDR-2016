import simpy
import random
import numpy as np
import matplotlib.pyplot as plt

class Packet(object):
	"""
	Packet Object
	time: packet creation time/ID (float)
	size: packet size (integer)
	dst: packet destination (string) - pkt_Receiver ID
	"""
	def __init__(self,time,size,dst):
		self.time=time
		self.size=size
		self.dst=dst

	def __repr__(self):
		return 'Pkt %f [%d] to %s'%(self.time,self.size,self.dst)

class Node(object):
	"""
	Node Object
	env: SimPy environment
	id: Node ID (string)
	speed: Node routing speed (float, pkts/sec)
	qsize: Node input queue size (integer, number of packets, default inf)
	"""
	def __init__(self,env,id,speed,qsize=np.inf):
		self.env=env
		self.id=id
		self.speed=speed
		self.qsize=qsize
		self.queue = simpy.Store(env)
		self.lost_pkts=0
		self.out={} #list with obj {'dest1':[elem1,elem3],'dest2':[elem1,elem2],...}
		self.action = env.process(self.run())

	def add_conn(self,elem,dsts):
		"""
		Defines node output connections to other simulation elements
		elem: Next element (object)
		dsts: list with destination(s) ID(s) accessible via elem (string or list of strings)
		"""
		for d in dsts:
			if self.out.has_key(d):
				self.out[d].append(elem)
			else:
				self.out.update({d:[elem]})

	def run(self):
		while True:
			pkt = (yield self.queue.get())
			yield self.env.timeout(1.0*pkt.size/self.speed)
			if self.out.has_key(pkt.dst):
				#random routing over all possible paths to dst
				outobj=self.out[pkt.dst][random.randint(0,len(self.out[pkt.dst])-1)]
				print(str(self.env.now)+': Packet out node '+self.id+' - '+str(pkt))
				outobj.put(pkt)
			else:
				print(str(self.env.now)+': Packet lost in node '+self.id+'- No routing path - '+str(pkt))

	def put(self,pkt):
		if len(self.queue.items)<self.qsize:
			self.queue.put(pkt)
		else:
			self.lost_pkts += 1
			print(str(env.now)+': Packet lost in node '+self.id+' queue - '+str(pkt))

class Link(object):
	"""
	Link Object
	env: SimPy environment
	id: Link ID (string)
	speed: Link transmission speed (float, bits/sec)
	qsize: Node to Link output queue size (integer, number of packets, default inf)
	"""
	def __init__(self,env,id,speed,qsize=np.inf):
		self.env=env
		self.id=id
		self.speed=1.0*speed/8
		self.qsize=qsize
		self.queue = simpy.Store(env)
		self.lost_pkts=0
		self.out=None
		self.action = env.process(self.run())

	def run(self):
		while True:
			pkt = (yield self.queue.get())
			yield self.env.timeout(1.0*pkt.size/self.speed)
			print(str(self.env.now)+': Packet out link '+self.id+' - '+str(pkt))
			self.out.put(pkt)

	def put(self,pkt):
		if len(self.queue.items)<self.qsize:
			self.queue.put(pkt)
		else:
			self.lost_pkts += 1
			print(str(self.env.now)+': Packet lost in link '+self.id+' queue - '+str(pkt))


class pkt_Sender(object):
	"""
	Packet Sender
	env: SimPy environment
	id: Sender ID (string)
	rate: Packet generation rate (float, packets/sec)
	dst: List with packet destinations (list of strings, if size>1 destination is random among all possible destinations)
	"""
	def __init__(self,env,id,rate,dst):
		self.env=env
		self.id=id
		self.rate=rate
		self.out=None
		self.dst=dst
		self.packets_sent=0
		self.action = env.process(self.run())

	def run(self):
		while True:
			yield self.env.timeout(np.random.exponential(1.0/self.rate))
			self.packets_sent += 1
			#size=random.randint(64,1500)
			#size=int(np.random.exponential(500))
			size=int(np.random.choice([64,1500],1,[.5,.5]))
			if len(self.dst)==1:
				dst=self.dst[0]
			else:
				dst=self.dst[random.randint(0,len(self.dst)-1)]
			pkt = Packet(self.env.now,size,dst)
			print(str(self.env.now)+': Packet sent by '+self.id+' - '+str(pkt))
			self.out.put(pkt)

class pkt_Receiver(object):
	"""
	Packet Receiver
	env: SimPy environment
	id: Sender ID (string)
	"""
	def __init__(self,env,id):
		self.env=env
		self.id=id
		self.queue = simpy.Store(env)
		self.packets_recv=0
		self.overalldelay=0
		self.overallbytes=0
		self.action = env.process(self.run())

	def run(self):
		while True:
			pkt = (yield self.queue.get())
			self.packets_recv += 1
			self.overalldelay += self.env.now-pkt.time
			self.overallbytes += pkt.size
			print(str(self.env.now)+': Packet received by '+self.id+' - '+str(pkt))

	def put(self,pkt):
		self.queue.put(pkt)


pkts_recv = [150,300,450]
queue_size = [64,96,128,10000]

lp_list = []
avg_list = []
trans_list =[]

loss_probability = []
avg_delay = []
trans_band = []

for i in pkts_recv:
	for j in queue_size:
		env = simpy.Environment()

		#Sender (tx) -> Node1 -> Link -> Receiver (rx)

		rx=pkt_Receiver(env,'B')
		tx=pkt_Sender(env,'A',i,'B')
		node1=Node(env,'N1',np.inf)
		link=Link(env,'L',2e6,j)

		tx.out=node1
		node1.add_conn(link,'B')
		link.out=rx

		print(node1.out)

		simtime=100
		env.run(simtime)

		loss_probability.append(100.0*link.lost_pkts/tx.packets_sent)
		avg_delay.append(1.0*rx.overalldelay/rx.packets_recv)
		trans_band.append(1.0*rx.overallbytes/simtime)

		print('Loss probability: %.2f%%'%(100.0*link.lost_pkts/tx.packets_sent))
		print('Average delay: %f sec'%(1.0*rx.overalldelay/rx.packets_recv))
		print('Transmitted bandwidth: %.1f Bytes/sec'%(1.0*rx.overallbytes/simtime))

	lp_list.append(loss_probability)
	avg_list.append(avg_delay)
	trans_list.append(trans_band)

	loss_probability = []
	avg_delay = []
	trans_band = []

# print lp_list
# print avg_list
# print trans_list

#stored_lp = [[0.0, 0.0, 0.0, 0.0], [0.07613373055279708, 0.0, 0.0, 0.0], [28.387767746503805, 29.065443452314682, 28.355719622842912, 26.77072694169368]]
#stored_avg_list = [[0.005680589746322665, 0.005837960156261968, 0.005733136554138936, 0.005762361160297351], [0.0424909320915409, 0.04883272060264993, 0.0463656895696208, 0.049909150481728955], [0.19571797717985354, 0.29046923713222356, 0.392399940169802, 2.9459918657566524]]
#stored_trans_list = [[117227.2, 118888.52, 116542.24, 119491.16], [233896.72, 234677.28, 234677.96, 235138.28], [249963.72, 249966.72, 249962.4, 249962.72]]

stored_lp = lp_list
stored_avg_list = avg_list
stored_trans_list = trans_list


tmp_pl = []
for i in stored_lp:
	tmp_pl.append(i[0])

tmp_ad = []
for i in stored_avg_list:
	tmp_ad.append(i[0])

# Lambda
fig, ax1 = plt.subplots()
ax1.plot(pkts_recv, tmp_pl, 'b')
ax1.set_xlabel('Pkts Incoming')
# Make the y-axis label and tick labels match the line color.
ax1.set_ylabel('Loss Packets %', color='b')
for tl in ax1.get_yticklabels():
    tl.set_color('b')

ax2 = ax1.twinx()

ax2.plot(pkts_recv, tmp_ad, 'r')
ax2.set_ylabel('Average Delay (seg)', color='r')
for tl in ax2.get_yticklabels():
    tl.set_color('r')

ax = plt.gca()

plt.show()

# Queue Size
fig, ax1 = plt.subplots()
ax1.plot(queue_size, stored_lp[2], 'b')
ax1.set_xlabel('Queue Size')
# Make the y-axis label and tick labels match the line color.
ax1.set_ylabel('Loss Packets %', color='b')
for tl in ax1.get_yticklabels():
    tl.set_color('b')

ax2 = ax1.twinx()

ax2.plot(queue_size, stored_avg_list[2], 'r')
ax2.set_ylabel('Average Delay (seg)', color='r')
for tl in ax2.get_yticklabels():
    tl.set_color('r')

ax = plt.gca()

plt.show()





