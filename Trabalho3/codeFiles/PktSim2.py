import simpy
import random
import decimal
import json
import numpy as np
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
        self.queue_sum = 0.0

    def run(self):
    	prev_time = 0
        while True:
            pkt = (yield self.queue.get())
            yield self.env.timeout(1.0*pkt.size/self.speed)
            #print(str(self.env.now)+': Packet out link '+self.id+' - '+str(pkt))
            self.out.put(pkt)
            self.queue_sum += len(self.queue.items) * (pkt.time-prev_time)
            prev_time = pkt.time

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


if __name__ == '__main__':

    pkts_recv = [150,300,450]
    queue_size = [64.0,96.0,128.0,10000.0]
    array = []
    lambd = pkts_recv[0]
    k = queue_size[0]

    for i in pkts_recv:
        for j in queue_size:
            lambd = i
            k = j

            print
            print
            print
            print "LAMBDA: " + str(lambd)
            print "QUEUE SIZE: " + str(k)
            print

            # m/m/1
            env = simpy.Environment()

            #Sender (tx) -> Node1 -> Link -> Receiver (rx)

            rx=pkt_Receiver(env,'B')
            tx=pkt_Sender(env,'A',lambd,'B')
            node1=Node(env,'N1',100,k)
            link=Link(env,'L',10e9)

            tx.out=node1
            node1.add_conn(link,'B')
            link.out=rx


            simtime=100
            env.run(simtime)
			
            lp = 100.0*node1.lost_pkts/tx.packets_sent
            ad = 1.0*rx.overalldelay/rx.packets_recv
            tqo = (link.queue_sum/simtime)/k
			
            print('Simulated Loss probability: %.2f%%'%(lp))
            print('Simulated Average delay: %f sec'%(ad))
            print('Simulated Transmitted Queue Occupation: %.1f'%(tqo))


            print "M/M/1"

            miu1 = 100 #2000000.0/(1500.0*8.0)

            #miu2 = 2000000.0/(64.0*8.0)

            inv_miu = 1/100

            ro = lambd*inv_miu

            R = 1.0/(miu1-lambd)
            
            queue_occ = (ro**2)/(1.0-ro)

            mm1ad = R
			
            print('Theorical Loss probability: %.2f%%'%(0))
            print('Theorical Average delay: %f sec'%(mm1ad))
            print('Theorical Queue occupation: %.1f '%(queue_occ/k))

            print "M/M/1/K"

            miu1 = 100

           

            inv_miu = 1.0*1/100


            ro = 1.0*lambd*inv_miu

            N = decimal.Decimal( decimal.Decimal( ro/(1.0-ro) ) - decimal.Decimal( decimal.Decimal( decimal.Decimal(k+1.0)* decimal.Decimal( ro)**decimal.Decimal(k+1.0)  ) ) / (decimal.Decimal(1.0)- decimal.Decimal(ro)**decimal.Decimal(k+1.0)  ) )

            R = N / decimal.Decimal( decimal.Decimal(lambd * decimal.Decimal( decimal.Decimal(1.0) - ( decimal.Decimal(1.0-ro)*decimal.Decimal(ro)**decimal.Decimal(k)) / ( decimal.Decimal(1.0) - decimal.Decimal(ro)**decimal.Decimal(k+1.0)))  ) )

            theorical_pkts_loss = 0
            for x in range(0,int(k)):
            	theorical_pkts_loss += decimal.Decimal(ro)**x * decimal.Decimal(decimal.Decimal(1.0-ro)/(decimal.Decimal(1.0)-decimal.Decimal(ro)**decimal.Decimal(k+1)))

            queue_occ = decimal.Decimal((ro)/(1.0-ro)) -decimal.Decimal(ro)*((decimal.Decimal(1.0)+decimal.Decimal(k)*decimal.Decimal(ro)**decimal.Decimal(k))/(decimal.Decimal(1.0)-decimal.Decimal(ro)**decimal.Decimal(k+1.0)))

            mm1kad = R
            mm1klp = (1-theorical_pkts_loss)*100

            print('Theorical Loss probability: %.2f%%'%(mm1klp))
            print('Theorical Average delay: %f sec'%(mm1kad))
            print('Theorical Queue occupation: %.1f '%(queue_occ/decimal.Decimal(k)))


            print "M/D/1"

            miu1 =100

            

            inv_miu = 1/100

            ro = lambd*inv_miu

            miu = 100

            R = (2.0*miu-lambd)/(2.0*miu*(miu-lambd))

            queue_occ = (ro**2)/((1.0-ro))

            md1ad = R

            print('Theorical Loss probability: %.2f%%'%(0))
            print('Theorical Average delay: %f sec'%(md1ad))
            print('Theorical Queue occupation: %.1f '%(queue_occ/k))

            print "M/G/1"

            miu1 = 10000000000.0/(1500.0*8.0)

            miu2 = 10000000000.0/(64.0*8.0)

            Es = (0.5*(1.0/miu1)) + (0.5*(1.0/miu2))
            Es2 = (0.5*(1.0/miu1))**2 + (0.5*(1.0/miu2))**2

            R = lambd*Es2/(2.0*(1.0-lambd*Es)) + Es

            queue_occ = (ro**2)/(1.0-ro)
			
            mg1ad = R
			
            print('Theorical Loss probability: %.2f%%'%(0))
            print('Theorical Average delay: %f sec'%(mg1ad))
            print('Theorical Queue occupation: %.1f '%(queue_occ/k))
			
            array = array + [{'lambda': lambd,
                              'queueSize': k,
                              'Loss probability': round(lp, 5),
                              'Average delay': round(ad, 5),
                              'Transmitted bandwidth': tqo,
                              'M/M/1 Loss': 0,
							  'M/M/1 Delay': round(mm1ad, 5),
                              'M/M/1/K Loss': round(mm1klp, 5),
							  'M/M/1/K Delay': round(mm1kad, 5),
							  'M/D/1 Loss': 0,
							  'M/D/1 Delay': round(md1ad, 5),
							  'M/G/1 Loss': 0,
							  'M/G/1 Delay': round(mg1ad, 5)}]
				  
with open('pktSim2.json', 'w') as outfile:
	json.dump(array, outfile)						  
#Em todos menos no mm1k, a fila e infinita, logo nao ha perdas