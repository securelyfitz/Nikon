#!/usr/bin/env python

import socket
import sys
import struct

def txn_counter():
	k = 0
	while True:
		k += 1
		yield k

txncount = txn_counter().next

def longhex(data):
	hexstring=''
	for i in range(len(data)):
		(byte,)=struct.unpack('B',data[i])
		hexstring += "{0:0>2x}:".format(byte)
		++i
	return hexstring

def txdata(s, data):
#	print 'txdata:', longhex(data) 
	s.send(struct.pack('I',len(data)+4)+data)

def rxdata(s):
#	need to rx one dword which will be size
	data=s.recv(4);
	(datalen,)=struct.unpack('I',data)
#	print "need to get ", datalen, "bytes, got ", len(data)," so far"
#	repeat until we get all data 
	while (datalen)>len(data):
#		rx size remaining dwords and return.
		data+=s.recv(datalen-len(data))
#		print "need to get ", datalen, "bytes, got ", len(data)," so far"
	return data[4:]

def txrxdata(s, data):
	txdata(s, data)
	return rxdata(s)

def initcmdreq(s):
	cmdtype=struct.pack('I',0x01)
	guid=struct.pack('LL',0x7766554433221100,0xffeeddccbbaa9988)
	compname='wmau/1.0.1.3002 (Android OS 4.0.4)\x00'
	computername=''
	for number in range(len(compname)):
		computername=computername+struct.pack('cB',compname[number],0x00)
	rxdata=txrxdata(s,cmdtype+guid+computername+struct.pack('I',0x01))
	if struct.unpack('I',rxdata[:4])==(2,):
#		print 'initcmdreq: Received:', longhex(rxdata[4:]) 
		return rxdata[4:]
	else:
		print "initcmdreq: bad response type: ",struct.unpack('I',rxdata[:4]),' not ',2,':',longhex(rxdata)
		sys.exit(1)

def initeventreq(s,sessionID):
	cmdtype=struct.pack('I',0x03)
	rxdata=txrxdata(s,cmdtype+sessionID)
	if struct.unpack('I',rxdata[:4])==(4,):
#		print 'initeventreq: received:', longhex(data), '\nascii:',data 
		return rxdata[4:]
	else:
		print "initeventreq: bad response type: ",struct.unpack('I',rxdata[:4]),' not ',4,':',longhex(rxdata)
		sys.exit(1)

def cmdreqnodata(s,command,args=''):
	cmdtype=0x06
	unknown=0x01
	txnid=txncount()
	rxresponse=txrxdata(s,struct.pack('IIH',cmdtype,unknown,command)+struct.pack('I',txnid)+args)
	(rxtype,rxcode)=struct.unpack('IH',rxresponse[:6])
	(rxtxn,)=struct.unpack('I',rxresponse[6:10])
	if rxtype!=0x07: 
		print "cmdreqnodata: response type ", rxtype, ' not 7:',longhex(rxresponse)
		sys.exit(1)
	if rxtxn!=txnid:
		print "cmdreqnodata: transaction id ", rxtxn,' not ',txnid,':',longhex(rxresponse)
		sys.exit(1)
#	print 'cmdreqnodata: received:', hex(rxcode) 
	return rxcode

def cmdreqsenddata(s,command,args='',data=''):
	print "args:", longhex(args)
	print "data:", longhex(data)
	#send command request with arguments
	cmdtype=0x06
	unknown=0x01
	txnid=txncount()
	txdata(s,struct.pack('IIH',cmdtype,unknown,command)+struct.pack('I',txnid)+args)
	
	#send data start with length of data
	cmdtype=0x09
	txdata(s,struct.pack('IIL',cmdtype,txnid,len(data)))

	#send data end with actual data
	cmdtype=0x0c
	txdata(s,struct.pack('II',cmdtype,txnid)+data)

	#get command response, check type and id
	rxresponse=rxdata(s)
#	print "cmdreqsenddata rxresponse: ",longhex(rxresponse)
	(rxtype,rxcode)=struct.unpack('IH',rxresponse[:6])
	(rxtxn,)=struct.unpack('I',rxresponse[6:10])
	if rxtype!=0x07: 
		print "cmdreqsenddata: response type ", rxtype, ' not 7:',longhex(rxresponse)
		sys.exit(1)
	if rxtxn!=txnid:
		print "cmdreqsenddata: transaction id ", rxtxn,' not ',txnid,':',longhex(rxresponse)
		sys.exit(1)

	#return response code, and response arguments
#	print 'cmdreqsenddata: response code:', hex(rxcode)
#	print 'cmdreqsenddata: response args:', rxresponse[10:]
	return (rxcode,rxresponse[10:])
	
def cmdreqgetdata(s,command,args=''):
#	print "cmdreqgetdata:",hex(command)
	cmdtype=0x06
	unknown=0x01
	txnid=txncount()

	#send request
	txdata(s,struct.pack('IIH',cmdtype,unknown,command)+struct.pack('I',txnid)+args)

	#get start data response, check type and ID, store length 
	rxstartdata=rxdata(s)
	(rxtype,rxtxn)=struct.unpack('II',rxstartdata[:8])
	if rxtype!=9: 
#		print "cmdreq: response type ", rxtype, ' not 9:',longhex(rxstartdata)
		return (cmdreqgetdata(s,command,args))
		sys.exit(1)
	if rxtxn!=txnid:
		print "cmdreq: transaction id ", rxtxn,' not ',txnid,':',longhex(rxstartdata)
		sys.exit(1)
	(rxsize,)=struct.unpack('I',rxstartdata[8:12])

	#get end data response, check type, id, and size from before
	rxenddata=rxdata(s)
	(rxtype,rxtxn)=struct.unpack('II',rxenddata[:8])
	if rxtype!=0x0c: 
		print "cmdreq: response type ", rxtype, ' not 12:',longhex(rxenddata)
		sys.exit(1)
	if rxtxn!=txnid:
		print "cmdreq: transaction id ", rxtxn,' not ',txnid,':',longhex(rxenddata)
		sys.exit(1)
	if len(rxenddata[8:])!=rxsize:
		print "cmdreq: data size is", len(rxenddata[8:]),' not ',rxsize,':',longhex(rxenddata)
		sys.exit(1)

	#get command response, check type and id
	rxresponse=rxdata(s)
	(rxtype,rxcode)=struct.unpack('IH',rxresponse[:6])
	(rxtxn,)=struct.unpack('I',rxresponse[6:10])
	if rxtype!=0x07: 
		print "cmdreq: response type ", rxtype, ' not 7:',longhex(rxresponse)
		sys.exit(1)
	if rxtxn!=txnid:
		print "cmdreq: transaction id ", rxtxn,' not ',txnid,':',longhex(rxresponse)
		sys.exit(1)

	#return data, response code, and response arguments
#	print 'cmdreqgetdata: response code:', hex(rxcode)
#	print 'cmdreqgetdata: response args:', rxresponse[10:]
#	print 'cmdreqgetdata: response data:', longhex(rxenddata[8:])
#	print 'cmdreqgetdata: response data:', rxenddata[8:]
	return (rxenddata[8:],rxcode,rxresponse[10:])

def connectptpip():
	host = 'localhost'
	host = '192.168.1.1'
	port = 15740
	s = None
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((host,port))
	except socket.error, (value,message):
		if s:
			s.close()
		print "Could not open socket: " + message
		sys.exit(1)
	return s


"""
s=connectptpip()
data=initcmdreq(s)
sessionid=data[:4]

s2=connectptpip()
data=initeventreq(s2,sessionid)

print "opening session"
data=cmdreqnodata(s,0x1002,sessionid)
print "startliveview: ", hex(cmdreqnodata(s,0x9201))
while (cmdreqnodata(s,0x90c8)==0x2019):
	pass
(data,code,response)=cmdreqgetdata(s,0x9203)
print "getliveviewimg:", hex(code)

s.close()
s2.close()
"""

