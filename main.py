import socket
import threading
import signal

import sys
import time

allowed_users = []
request_url_time = {}
cache = {}


def modified(url):
	if url in cache:
		s.send("GET /" + url + " HTTP/1.1\r\nIf-Modified-Since: " + cache[url][-1] + " \r\n\r\n")
	else:
		return False
	reply = s.recv(100000)
	if reply.find("200") >= 0:
		return True
	else:
		return False

def to_cache(url):
	if url not in request_url_time:
		request_url_time[url] = [time.time()]
	else:
		request_url_time[url].append(time.time())
		if len(request_url_time[url]) > 3:
			request_url_time[url].pop(0)
			if request_url_time[url][2] - request_url_time[url][0] <= 300:
				return True
	return False

def fill_cache(url, data):
	if(len(cache) < 3):
		cache[url] = [data, time.time()]
	else:
		old_key = -1
		old_time = time.time()
		for key in cache:
			if cache[key][1] < old_time:
				old_key = key
				old_time = cache[key][1]
		del cache[old_key]
		cache[url] = [data, time.time()]


# fills the allowed username/password
def fill_allowed_users():
	with open('proxy/allowed_users.txt', 'r') as f:
		for line in f:
			line = line.split(' ')
			if len(line) != 2:
				print "Problem in allowed_users.txt"
				return
			allowed_users.append([line[0], line[1]])

# check if username and password are correct
def authenticated_user(user_data):
	print str(user_data)
	with open('proxy/allowed_users.txt', 'r') as f:
		for line in f:
			if(str(user_data) == str(line)[:-1]):
				print "Access Granted"
				return True
	print "Access Denied"
	return False

# checks if given ip is blacklisted
def blacklist(ip):
	with open('proxy/blacklist.txt', 'r') as f:
		for line in f:
			line = line.split(':')[1]
			if(str(ip) == str(line)[:-1]):
				print "Match Found"
				return True
	return False

def get_url(data): # get url from http request
	data = data.split('\n')[0]
	data = data.split(" ")[1]
	return data

def get_ip_port(url): # get ip and port number from the url
	http_pos = url.find("://")
	if (http_pos==-1):
		temp = url
	else:
		temp = url[(http_pos+3):]

	port_pos = temp.find(":")

	webserver_pos = temp.find("/")
	if webserver_pos == -1:
		webserver_pos = len(temp)

	webserver = ""
	port = -1
	if (port_pos==-1 or webserver_pos < port_pos): 

		port = 80 
		webserver = temp[:webserver_pos] 

	else:
		port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
		webserver = temp[:port_pos] 
	return webserver, port


class Server():
	def __init__(self):
		signal.signal(signal.SIGINT, self.shutdown) 
		try:
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error as err:
			print "socket creation failed with error", err
		self.port = 20100
		self.socket.bind(('', self.port))
		self.print_lock = threading.Lock()

	def shutdown(self, signum, frame):
		main_thread = threading.currentThread()
		for t in threading.enumerate():
			if t is main_thread:
				continue
			t.join()
		self.socket.close()
		sys.exit(0)

	def listen(self,max_connections):
		self.socket.listen(max_connections)

		while True:
			actual_client, addr = self.socket.accept() # accepting a client

			# if int(addr[1]) > 20100 or int(addr[1]) < 20000: # blocking requests from outside IIIT
			#   print "Received connection is not from IIIT\n"
			#   actual_client.send("You are not allowed to access this server$")
			#   actual_client.close()
			#   continue

			print 'Got connection from ip', addr[0], " and port ", addr[1]

			data = actual_client.recv(1024)
			url = get_url(data)
			ip, port = get_ip_port(url) # extracted ip and port number

			if blacklist(port): # if requested ip is blacklisted then ask for username and password
				actual_client.send("Please enter username and password with a space between them\n")
				user_data = actual_client.recv(1024)
				# print "FUCK"
				# user_data = user_data.split(' ')

				if not authenticated_user(user_data): # if username/password is wrong then send error message
					print"mddjk"
					actual_client.send("Your username or password is wrong\n This url is blocked!!\n$\n")
					actual_client.close()
					continue

			if url in cache and  not modified(url):
				data = cache[url][0]
				actual_client.send(data)
				actual_client.close()
				
			t1 = threading.Thread(target=self.connect_to_server, args=(actual_client, ip, port, data,url))
			t1.start()

	def connect_to_server(self,actual_client, ip, port, data,url): # connect to the server and get data
		c = Client(ip, port, data)
		c.cnct(1024, actual_client,url)
		actual_client.close()


class Client():
	def __init__(self,dest_addr, dest_port, data):
		try:
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error as err:
			print "socket creation failed with error %s" % (err)
		self.port = 20100
		self.dest_addr = socket.gethostbyname(dest_addr)
		self.dest_port = dest_port
		self.data = data

	def cnct(self,data_size, actual_client,url): # connect to server, get data and send back to client
		self.socket.connect((self.dest_addr, self.dest_port))
		self.socket.sendall(self.data)
		s = ""
		while True:
			rec_data = self.socket.recv(data_size)
			if(len(rec_data) > 0):
				actual_client.send(rec_data)
				s+=rec_data
			else:
				break
			if(len(rec_data) < data_size):
				break



		if to_cache(url):
			fill_cache(url,s)

		actual_client.send("$\n")
		self.socket.close()

def main():
	fill_allowed_users()
	print allowed_users
	print "jkjdkjs"
	s = Server()
	print "jkjdkjs"
	s.listen(5)
	print "jkjdkjs"



if __name__== "__main__":
	main()



