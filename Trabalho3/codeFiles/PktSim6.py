import simpy
import sys
import random
import numpy as np

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
			yield self.env.timeout(1.0/self.speed)
			if self.out.has_key(pkt.dst):
				#random routing over all possible paths to dst
				outobj=self.out[pkt.dst][random.randint(0,len(self.out[pkt.dst])-1)]
				#print(str(self.env.now)+': Packet out node '+self.id+' - '+str(pkt))
				outobj.put(pkt)
			else:
				#print(str(self.env.now)+': Packet lost in node '+self.id+'- No routing path - '+str(pkt))
				pass

	def put(self,pkt):
		if len(self.queue.items)<self.qsize:
			self.queue.put(pkt)
		else:
			self.lost_pkts += 1
			#print(str(env.now)+': Packet lost in node '+self.id+' queue - '+str(pkt))

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
			#print(str(self.env.now)+': Packet out link '+self.id+' - '+str(pkt))
			self.out.put(pkt)

	def put(self,pkt):
		if len(self.queue.items)<self.qsize:
			self.queue.put(pkt)
		else:
			self.lost_pkts += 1
			#print(str(self.env.now)+': Packet lost in link '+self.id+' queue - '+str(pkt))


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
			#print(str(self.env.now)+': Packet sent by '+self.id+' - '+str(pkt))
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
			#print(str(self.env.now)+': Packet received by '+self.id+' - '+str(pkt))

	def put(self,pkt):
		self.queue.put(pkt)

def main():
	pkts_recvA = [150,300,450,600]
	pkts_recvB = [150,300,450,600]
	queue_size = [64,96,128,192,256]
	router_speed = [500,750,1000]

	sys.stdout = Logger("ex13.txt")

	for i in pkts_recvA:
		for j in pkts_recvB:
			for l in queue_size:
				for m in router_speed:
					lambdA = i
					lambdB = j

					k = l
					R = m

					print "lambdA: " + str(lambdA) + "; lambdB: " + str(lambdB) + "; Queue Size: " + str(k) + "; Routing Speed: " + str(R)

					env = simpy.Environment()

					#Sender (tx) -> Node1 -> Link -> Receiver (rx)

					rx=pkt_Receiver(env,'Internet')
					tx1=pkt_Sender(env,'A',lambdA,'Internet')
					tx2=pkt_Sender(env,'B',lambdB,'Internet')

					node1=Node(env,'N1',R,k)
					node2=Node(env,'N2',R,k)
					node3=Node(env,'N3',R,k)
					node4=Node(env,'N4',R,k)

					link1=Link(env,'L1',10e6,k)
					link2=Link(env,'L2',10e6,k)
					link3=Link(env,'L3',10e6,k)
					link4=Link(env,'L4',10e6,k)

					tx1.out=node1
					tx2.out=node2

					node1.add_conn(link1,'Internet')
					node2.add_conn(link2,'Internet')

					link1.out=node3
					link2.out=node3

					node3.add_conn(link3,'Internet')

					link3.out=node4

					node4.add_conn(link4,'Internet')
					link4.out=rx


					#print(node1.out)

					simtime=100
					env.run(simtime)


					lost_pkts = (link1.lost_pkts + link2.lost_pkts + link3.lost_pkts + link4.lost_pkts + node1.lost_pkts + node2.lost_pkts + node3.lost_pkts + node4.lost_pkts)*1.0 / ((tx1.packets_sent + tx2.packets_sent)*1.0)

					avg_delay = 1.0*rx.overalldelay/rx.packets_recv

					print('Loss probability: %.2f%%'%(100.0*lost_pkts))
					print('Average delay: %f sec'%(avg_delay))

					print
					print

	sys.stdout.close()


class Logger(object):
    def __init__(self, fname):
        self.terminal = sys.stdout
        self.log = open(fname, "w+")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def close(self):
        self.log.close()

if __name__ == '__main__':
	main()

