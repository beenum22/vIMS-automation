import os
import sys
import select
import time
import readline
import json
from datetime import datetime
import time

#function for configuration input from creds.txt file

def input_configurations(error_logger, logger):
	try:
		json_file = open('configurations.json')
	except:
         print "configuration.json: file not found"
         error_logger.exception("configuration.json: file not found")
         sys.exit()
	
	configurations = json.load(json_file)
	
	try:
		logger.info("Getting credentials from file")
		file_read = open('creds.txt')
	except:
		print "creds.txt: file not found"
		error_logger.exception("creds.txt: file not found")
		sys.exit()
	
	for i in range(1, 10):
		inp = file_read.readline()
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['os-creds']['os-authurl'] = inp[1]
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['os-creds']['os-user-name'] = inp[1]
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['os-creds']['os-tenant-name'] = inp[1]
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['os-creds']['os-pass'] = inp[1]
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['net-ext-name'] = inp[1]

	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['net-int-cidr'] = inp[1]
	name = configurations['networks']['net-int-name']
	cidr = configurations['networks']['net-int-cidr']
	(pool_start, pool_stop) = cal_ip_pool(name, cidr, logger)
	configurations['networks']['net-int-pool-start'] = pool_start
	configurations['networks']['net-int-pool-end'] = pool_stop

	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['s1c-cidr'] = inp[1]
	name = configurations['networks']['s1c-name']
	cidr = configurations['networks']['s1c-cidr']
	(pool_start, pool_stop) = cal_ip_pool(name, cidr, logger)
	configurations['networks']['s1c-pool-start'] = pool_start
	configurations['networks']['s1c-pool-end'] = pool_stop

	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['s1u-cidr'] = inp[1]
	name = configurations['networks']['s1u-name']
	cidr = configurations['networks']['s1u-cidr']
	(pool_start, pool_stop) = cal_ip_pool(name, cidr, logger)
	configurations['networks']['s1u-pool-start'] = pool_start
	configurations['networks']['s1u-pool-end'] = pool_stop
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['s6a-cidr'] = inp[1]
	name = configurations['networks']['s6a-name']
	cidr = configurations['networks']['s6a-cidr']
	(pool_start, pool_stop) = cal_ip_pool(name, cidr, logger)
	configurations['networks']['s6a-pool-start'] = pool_start
	configurations['networks']['s6a-pool-end'] = pool_stop
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['radius-cidr'] = inp[1]
	name = configurations['networks']['radius-name']
	cidr = configurations['networks']['radius-cidr']
	(pool_start, pool_stop) = cal_ip_pool(name, cidr,logger)
	configurations['networks']['radius-pool-start'] = pool_start
	configurations['networks']['radius-pool-end'] = pool_stop
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['sgs-cidr'] = inp[1]
	name = configurations['networks']['sgs-name']
	cidr = configurations['networks']['sgs-cidr']
	(pool_start, pool_stop) = cal_ip_pool(name, cidr, logger)
	configurations['networks']['sgs-pool-start'] = pool_start
	configurations['networks']['sgs-pool-end'] = pool_stop
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['sgi-cidr'] = inp[1]	
	name = configurations['networks']['sgi-name']
	cidr = configurations['networks']['sgi-cidr']
	(pool_start, pool_stop) = cal_ip_pool(name, cidr,logger)
	configurations['networks']['sgi-pool-start'] = pool_start
	configurations['networks']['sgi-pool-end'] = pool_stop

	logger.info("Writing configurations from text file to configuration.json")
	with open('configurations.json', 'w') as outfile:
		json.dump(configurations, outfile, indent=4)
	file_read.close()

	
'''
	#vcm_cfg_file_read = open('range_nexthop.txt', 'r').readlines()
	try:
		param_file_write = open('source/vEPC_deploy/ip_files/range_nexthop.txt', 'w')
	except:
		print "source/vEPC_deploy/ip_files/range_nexthop.txt: file not found"
		error_logger.exception("source/vEPC_deploy/ip_files/range_nexthop.txt: file not found")
		#sys.exit()
	inp = file_read.readline()
	param_file_write.write(inp)
	
	inp = file_read.readline()
	param_file_write.write(inp)
	
	logger.info("writing to configuration file")
	json_file.close()
	param_file_write.close()
'''

	
#--------------------------------------------------------#

#===========calculate IP pool============#
def cal_ip_pool(netname, cidr,logger):
	net_addr = calculate_subnet_address('network_add', cidr, logger)
	mask = calculate_subnet_address('mask', cidr, logger)
	logger.info("Calculating IP pool of network + " + netname +" " +cidr )
	mask = mask.split(".")
	net_address = net_addr
	net_addr = net_addr.split(".")
	
	available_ips = 255 - int(mask[3])
	
	if (available_ips < 30):
		print("Please enter cidr value less than or equal to 27 ... e.g. 10.1.1.0/27")
		sys.exit()
	ip_pool_start = net_addr[0] +'.' + net_addr[1] +'.' + net_addr[2] +'.' + str( int(net_addr[3]) + 4)
	ip_pool_end = net_addr[0] +'.' + net_addr[1] +'.' + net_addr[2] +'.' + str( int(net_addr[3]) + 21)
	
	list_ips = get_available_IP(net_address, mask[3], logger)
	
	write_ip_file(list_ips, netname)
	return (ip_pool_start, ip_pool_end)
	
#=========================================#
#=============find available IPs list=========#
def get_available_IP(net_addr, mask, logger):
	logger.info("Calculating available IPs in " + net_addr)
	list_ips = ''
	net_addr = net_addr.split(".")
	netw_addr = net_addr[0] + '.' + net_addr[1] + '.' + net_addr[2] + '.'
	rng = 255 - int(mask)
	#max_ip = 255 - mask - 20
	pool = int(net_addr[3]) + 22
	for i in range (pool, rng):
		ip = netw_addr + str(i)
		list_ips = list_ips + ip + '\n'
	
	return list_ips

#===========================================#
#=============write available IP list to file=========#
def write_ip_file(list_ips, netname):
	filename = 'source/vEPC_deploy/ip_files/' + netname + '_available_ips.txt'
	target = open(filename, 'w')
	target.write(list_ips)
	target.close()
#=======================================================#
#-------------------calculate subnet mask---------------#
def calculate_subnet_address(name, net_cidr, logger):
	logger.info("Calculating subnet of net " + name + " " + net_cidr)
	(addrString, cidrString) = net_cidr.split('/')
	addr = addrString.split('.')
	cidr = int(cidrString)
	
	# Initialize the netmask and calculate based on CIDR mask
	mask = [0, 0, 0, 0]
	for i in range(cidr):
		mask[i/8] = mask[i/8] + (1 << (7 - i % 8))
	if name == 'mask':
		return ".".join(map(str, mask))

	# Initialize net and binary and netmask with addr to get network
	net = []
	for i in range(4):
		net.append(int(addr[i]) & mask[i])
	if name == 'network_add':
		return ".".join(map(str, net))

#-------------------------------------------------------------------#