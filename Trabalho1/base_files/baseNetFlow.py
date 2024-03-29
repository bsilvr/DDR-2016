# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import socket
import struct
import argparse
from netaddr import IPNetwork, IPAddress


def printMatrix(m):
    print ("|||(src/dst)||||", end="")
    for j in m.keys():
        print ("|--%s--" % j, end="")
    print ("|", end="\n")

    for i in m.keys():
        print ("|--%s--| " % i, end="")
        for j in m.keys():
            print (m[i][j], end="")
            print ("       ", end="")
        print ("", end="\n")




def int_to_ipv4(addr):
    return "%d.%d.%d.%d" % \
       (addr >> 24 & 0xff, addr >> 16 & 0xff, \
        addr >> 8 & 0xff, addr & 0xff)

def getNetFlowData(data):
    sdata=struct.unpack("!H", data[:2])
    version = sdata[0]

    if version==1:
        print("NetFlow version %d:"%version)
        hformat="!HHIII"
        # ! - network (= big-endian), H – C unsigned short (2 bytes), I – C unsigned int (4 bytes)
        hlen = struct.calcsize(hformat)
        if len(data) < hlen:
            print("Truncated packet (header)")
            return 0,0
        sheader= struct.unpack(hformat, data[:hlen])
        version = sheader[0]
        num_flows = sheader[1]
        #more header

        print(num_flows)
        fformat="!IIIHHIIIIHHHBBBBBBI"
        # B – C unsigned char (1 byte)
        flen=struct.calcsize(fformat)

        if len(data) - hlen != num_flows * flen:
            print("Packet truncated (flows data)")
            return 0,0

        flows={}
        for n in range(num_flows):
            flow={}
            offset = hlen + flen*n
            fdata = data[offset:offset + flen]
            sflow=struct.unpack(fformat, fdata)
            flow.update({'src_addr':int_to_ipv4(sflow[0])})
            flow.update({'dst_addr':int_to_ipv4(sflow[1])})
            flow.update({'next_hop':int_to_ipv4(sflow[2])})
            flow.update({'in_idx': sflow[3]})
            flow.update({'out_idx': sflow[4]})
            flow.update({'flow_pkts':sflow[5]})
            flow.update({'flow_octets':sflow[6]})
            flow.update({'start': sflow[7]})
            flow.update({'finish': sflow[8]})
            flow.update({'scr_port':sflow[9]})
            flow.update({'dst_port':sflow[10]})
            flow.update({'protocol': sflow[12]})
            flow.update({'ToS': sflow[13]})
            flow.update({'flags': sflow[14]})

            #more flow
            flows.update({n:flow})
    else:
        print("NetFlow version %d not supported!"%version)

    out=version,flows
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('-p', '--port', nargs='?',type=int,help='listening UDP port',default=9996)
    parser.add_argument('-n', '--net', nargs='+',required=True, help='networks')
    parser.add_argument('-r', '--router', nargs='+',required=True, help='IP address(es) of NetFlow router(s)')
    args=parser.parse_args()

    nets=[]
    for n in args.net:
        try:
            nn=IPNetwork(n)
            nets.append(nn)
        except:
            print('%s is not a network prefix'%n)
    print(nets)
    if len(nets)==0:
        print("No valid network prefixes.")
        sys.exit()

    router=[]
    for r in args.router:
        try:
            rr=IPAddress(r)
            router.append(rr)
        except:
            print('%s is not an IP address'%r)
    print(router)
    if len(router)==0:
        print("No valid router IP address.")
        sys.exit()

    matrix = {}
    for i in nets:
        matrix[str(i)] = {}
        for j in nets:
            matrix[str(i)][str(j)] = [0,0,0]

    printMatrix(matrix)



    udp_port=args.port
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # UDP
    sock.bind(('0.0.0.0', udp_port))
    print("listening on '0.0.0.0':%d"%udp_port)

    try:
        while 1:
            data, addr = sock.recvfrom(8192)        # buffer size is 8192 bytes
            version,flows=getNetFlowData(data)      #version=0 reports an error!
            print('Version: %d'%version)
            print(flows)

            for n in nets:
                if IPAddress(flows[0]['src_addr']) in n:
                    for i in nets:
                        if IPAddress(flows[0]['dst_addr']) in i:
                            matrix[str(i)][str(n)][0] += 1
                            matrix[str(i)][str(n)][1] += flows[0]['flow_pkts']
                            matrix[str(i)][str(n)][2] += flows[0]['flow_octets']

            printMatrix(matrix)


    except KeyboardInterrupt:
        sock.close()
        print("\nDone!")

if __name__ == "__main__":
    main()
