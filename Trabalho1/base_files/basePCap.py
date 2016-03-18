import sys
import argparse
import pyshark
import numpy as np
from netaddr import IPNetwork, IPAddress, IPSet

npkts=0
downloadTick=0
uploadTick=0
downloadTotal=0
uploadTotal=0
tick=10
targetDownload = open("Download", 'w+')
targetUpload = open("Upload", 'w+')
first=True
downloadValues= []

def pkt_callback(pkt):
	global scnets
	global ssnets
	global npkts
	global downloadTick
	global uploadTick
	global downloadTotal
	global uploadTotal
	global tick
	global targetDownload
	global targetUpload
	global first
	global downloadValues


	if IPAddress(pkt.ip.src) in scnets|ssnets and IPAddress(pkt.ip.dst) in scnets|ssnets:
		npkts=npkts+1
		if first:
			tick = float(pkt.sniff_timestamp)
			first = False
		else:
			diference = float(pkt.sniff_timestamp) - float(tick)

			if diference > 1:
				if diference > 2:
					i=1
					while i < diference:
						downloadValues.append(0)
						targetDownload.write("0")
						targetUpload.write("0")
						targetDownload.write("\n")
						targetUpload.write("\n")
						i=i+1

				downloadValues.append(float(downloadTick))
				targetDownload.write(str(downloadTick))
				targetDownload.write("\n")
				targetUpload.write(str(uploadTick))
				targetUpload.write("\n")

				downloadTick = 0
				uploadTick = 0
				tick = pkt.sniff_timestamp

			if IPAddress(pkt.ip.src) in ssnets:

				downloadTick=downloadTick+int(pkt.ip.len)
				downloadTotal=downloadTotal+int(pkt.ip.len)

			if IPAddress(pkt.ip.dst) in ssnets:

				uploadTick=uploadTick+int(pkt.ip.len)
				uploadTotal=uploadTotal+int(pkt.ip.len)

			if pkt.ip.proto=='17':
				print('%s: IP packet from %s to %s (UDP:%s) %s'%(pkt.sniff_timestamp,pkt.ip.src,pkt.ip.dst,pkt.udp.dstport,pkt.ip.len))
			elif pkt.ip.proto=='6':
				print('%s: IP packet from %s to %s (TCP:%s) %s'%(pkt.sniff_timestamp,pkt.ip.src,pkt.ip.dst,pkt.tcp.dstport,pkt.ip.len))
			else:
				print('%s: IP packet from %s to %s (other) %s'%(pkt.sniff_timestamp, pkt.ip.src,pkt.ip.dst,pkt.ip.len))



def main():
	parser=argparse.ArgumentParser()
	parser.add_argument('-i', '--interface', nargs='?',required=True, help='capture interface')
	parser.add_argument('-c', '--cnet', nargs='+',required=True, help='client network(s)')
	parser.add_argument('-s', '--snet', nargs='+',required=True, help='service network(s)')
	parser.add_argument('-t', '--tcpport', nargs='?',help='service TCP port (or range)')
	parser.add_argument('-u', '--udpport', nargs='?',help='service UDP port (or range)')
	args=parser.parse_args()

	cnets=[]
	for n in args.cnet:
		try:
			nn=IPNetwork(n)
			cnets.append(nn)
		except:
			print('%s is not a network prefix'%n)
	print(cnets)
	if len(cnets)==0:
		print("No valid client network prefixes.")
		sys.exit()
	global scnets
	scnets=IPSet(cnets)

	snets=[]
	for n in args.snet:
		try:
			nn=IPNetwork(n)
			snets.append(nn)
		except:
			print('%s is not a network prefix'%n)
	print(snets)
	if len(snets)==0:
		print("No valid service network prefixes.")
		sys.exit()

	global ssnets
	ssnets=IPSet(snets)

	if args.udpport is not None:
		cfilter='udp portrange '+args.udpport
	elif args.tcpport is not None:
		cfilter='tcp portrange '+args.tcpport
	else:
		cfilter='ip'

	cint=args.interface
	print('Filter: %s on %s'%(cfilter,cint))

	try:
		capture = pyshark.LiveCapture(interface=cint,bpf_filter=cfilter)
		capture.apply_on_packets(pkt_callback)
	except KeyboardInterrupt:
		global npkts
		global downloadTotal
		global uploadTotal
		global targetDownload
		global targetUpload
		global downloadValues
		targetDownload.close()
		targetUpload.close()
		print('\n%d packets captured! Done!\n Download: %d Bytes\n Upload: %d Bytes'%(npkts, downloadTotal, uploadTotal))

if __name__ == '__main__':
    main()
