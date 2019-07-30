import socket			 

s = socket.socket()		 
print "Socket successfully created"

port = 12345		

s.bind(('', port))		 
print "socket binded to %s" %(port) 

s.listen(5)	 
print "socket is listening"			


while True: 

	c, addr = s.accept()	
	rec_data = s.recv(19090)

	if "If-Modified-Since" in rec_data:
		print "Checked for modified data"
		c.send('304')

	rr = s.recv(19090)

	if "POST" in rr:
		print "data printed"

	print 'Got connection from', addr 

	c.send('Thank you for connecting') 

	c.close() 

