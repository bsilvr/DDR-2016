import simpy
import random
import numpy as np
import sys
import decimal
#import matplotlib.pyplot as plt

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
                pass
                #print(str(self.env.now)+': Packet lost in node '+self.id+'- No routing path - '+str(pkt))

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

class Logger(object):
    def __init__(self, fname):
        self.terminal = sys.stdout
        self.log = open(fname, "w+")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def close(self):
        self.log.close()






sys.stdout = Logger("ex9.txt")

pkts_recv = [150,300,450]
queue_size = [64,96,128,10000]

#Sender (tx) -> Node1 -> Link -> Receiver (rx)

simtime=100

for i in pkts_recv:
    for j in queue_size:
        env = simpy.Environment()

        print "Lambda: " + str(i) + ";  Queue: " + str(j)
        lambd = i
        k = j

        rx=pkt_Receiver(env,'B')
        tx=pkt_Sender(env,'A',lambd,'B')
        node1=Node(env,'N1',np.inf)
        node2=Node(env,'N2',np.inf)
        link1=Link(env,'L1',2e6,k)
        link2=Link(env,'L2',2e6,k)

        tx.out=node1
        node1.add_conn(link1,'B')
        link1.out=node2
        node2.add_conn(link2,'B')
        link2.out = rx

        env.run(simtime)

        miu = 2000000/(0.5*1500.0*8.0 + 0.5*64.0*8.0)

        W = 2/(miu-lambd)

        ro = lambd/miu
        print "Theorical average delay: %f"%W

        theorical_pkts_loss = 0
        for x in range(0,int(k)):
            theorical_pkts_loss += decimal.Decimal(ro)**x * decimal.Decimal(decimal.Decimal(1.0-ro)/(decimal.Decimal(1.0)-decimal.Decimal(ro)**decimal.Decimal(k+1)))


        print "Theorical packet loss: %.2f%%" % ((1.0-float(theorical_pkts_loss))*100)

        link1_loss = (100.0*link1.lost_pkts/tx.packets_sent)
        link2_loss = (100.0*link2.lost_pkts/tx.packets_sent)

        print('Loss probability Link 1: %.2f%%'%link1_loss)
        print('Loss probability Link 2: %.2f%%'%link2_loss)
        print('Total loss probability: %.2f%%'%(link1_loss+link2_loss))
        print('Average delay: %f sec'%(1.0*rx.overalldelay/rx.packets_recv))

        print
        print
        print

sys.stdout.close()





