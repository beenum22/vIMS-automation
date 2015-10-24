#------------python lib imports-----------#
import os
import time
import select
import sys
from collections import namedtuple
import readline
import paramiko
import json
import logging
import datetime
import time
#-----------------------------------------#
#-------------functions import-------------#
from os_defs import *
from consts import *
from funcs import *
from vcm_defs import *
#-----------------------------------------#

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

	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['s1c-cidr'] = inp[1]

	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['s1u-cidr'] = inp[1]
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['s6a-cidr'] = inp[1]
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['radius-cidr'] = inp[1]
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['sgs-cidr'] = inp[1]
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['sgi-cidr'] = inp[1]

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
	with open('configurations.json', 'w') as outfile:
		json.dump(configurations, outfile, indent=7)
	param_file_write.close()
	
	file_read.close()
#--------------------------------------------------------#

# get configurations from json file
def get_configurations(logger, error_logger):
	try:
		logger.info("Getting configurations from file")
		file = open('configurations.json')
	except:
		print "configuration.json: file not found"
		error_logger.exception("configuration.json: file not found")
		sys.exit()
	configurations = json.load(file)
	file.close()
	return configurations
#-------------------------------------#
#===========calculate IP pool============#
def cal_ip_pool(netname, cidr, configurations):
	
	net_addr = calculate_subnet_address('network_add', cidr)
	mask = calculate_subnet_address('mask', cidr)
	
	ip_pool_start = ''
	ip_pool_end = ''
	
	mask = mask.split(".")
	net_address = net_addr
	net_addr = net_addr.split(".")
	
	available_ips = 255 - int(mask[3])
	
	if (available_ips < 30):
		print("Please enter cidr value less than or equal to 27 ... e.g. 10.1.1.0/27")
		sys.exit()
	if (netname == configurations['networks']['net-int-name']):
		ip_pool_start = net_addr[0] +'.' + net_addr[1] +'.' + net_addr[2] +'.' + str(int(net_addr[3]) + 2)
		ip_pool_end = net_addr[0] +'.' + net_addr[1] +'.' + net_addr[2] +'.' + str(int(net_addr[3]) + 254)
	else:
		ip_pool_start = net_addr[0] +'.' + net_addr[1] +'.' + net_addr[2] +'.' + str(int(net_addr[3]) + 4)
		ip_pool_end = net_addr[0] +'.' + net_addr[1] +'.' + net_addr[2] +'.' + str(int(net_addr[3]) + 21)
		list_ips = get_available_IP(net_address, mask[3])
		write_ip_file(list_ips, netname)
	
	#avl_ip_range = 255 - (mask[3]+22)
	return (ip_pool_start, ip_pool_end)
	
#=========================================#
#=============find available IPs list=========#
def get_available_IP(net_addr, mask):
	
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
def calculate_subnet_address(name, net_cidr):
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
'''
#--------create availaible IPs file-------#
def create_IP_file(netname, configurations, logger):
	info_msg = "Creating IP file " + netname
	logger.info(info_msg)
	net_cidr = ''
	if netname == 's1':
		net_cidr = configurations['networks']['s1-cidr']
	elif netname == 'sgi':
		net_cidr = configurations['networks']['sgi-cidr']
	
	net_addr = calculate_subnet_address('network_add', net_cidr)
	subnet_mask = calculate_subnet_address('mask', net_cidr)
	subnet_mask = subnet_mask.split('.')
	pool = ''
	
	filename = 'source/vEPC_deploy/ip_files/'
	if 's1' in netname:
		filename = filename + 's1_available_ips.txt'
		s1_e = configurations['networks']['s1_pool_end'].split('.')
		pool =  int(s1_e[3])
	elif 'sgi' in netname:
		filename = filename + 'sgi_available_ips.txt'
		sgi_e = configurations['networks']['sgi_pool_end'].split('.')
		pool =  int(sgi_e[3])# - int(sgi_s[3])
		
	ip_list = get_available_IP(net_addr, int(subnet_mask[3]), pool)
	target = open(filename, 'w')
	#target.truncate()
	target.write(ip_list)
	target.close()
	logger.info("Done creating IP file for " + netname + " ...")
#-----------------------------------#
'''
#------- getting available IP for DELL VCM config file-----#
def get_IP_from_file(f_name):
	
	filename = ''
	
	if (f_name == 's1'):
		filename = 'source/vEPC_deploy/ip_files/s1_available_ips.txt'
	elif (f_name == 'sgi'):
		filename = 'source/vEPC_deploy/ip_files/sgi_available_ips.txt'

	file_read = open(filename, 'r')
	assigned_ip = file_read.readline()
	
	str1 = file_read.read()
	file_read.close()
	list_str = str1.split("\n")
	
	file_write = open(filename, 'w')

	for i in range (0 , len(list_str)):
		#new_line = file_read.readline()
		new_line = list_str[i] + '\n'
		file_write.write(new_line)
	
	file_read.close()
	file_write.close()
	
	return assigned_ip
#--------------------------------#
#-------------------writing IP of VCM config to separate file---------#
def write_cfg_file(cfg_file_name, configurations, nova, neutron):
	ip_filename = ''
	sgi_ip = ''
	
	s1_ip_filename = 'source/vEPC_deploy/ip_files/s1c_assigned_ips.txt'
	sgi_ip_filename = 'source/vEPC_deploy/ip_files/sgi_assigned_ips.txt'
	
	s1_ip_file = open(s1_ip_filename, 'a')
	sgi_ip_file = open(sgi_ip_filename, 'a')
		
	param_file_read = open('source/vEPC_deploy/ip_files/range_nexthop.txt', 'r')
	
	inp = param_file_read.readline()
	inp = inp.split("\"")
	
	vcm_cfg_file_read = open(cfg_file_name, 'r').readlines()
	vcm_cfg_file_write = open(cfg_file_name, 'w')
	
	net_name = configurations['networks']['net-int-name']
	ems_name = configurations['vcm-cfg']['ems-vm-name']
	server = nova.servers.find(name=ems_name).addresses
	ems_private_ip = server[net_name][0]['addr']
	
	for line in vcm_cfg_file_read:
		if line.startswith("ems rest"):
			new_line = "ems rest ip-address " + ems_private_ip
			vcm_cfg_file_write.write(new_line)
		
		elif line.startswith("range"):
			new_line = "range " + inp[1] + '\n'
			vcm_cfg_file_write.write(new_line)
		
		elif line.startswith("nexthop address"):
			inp = param_file_read.readline()
			inp = inp.split("\"")
			new_line = "nexthop address " + inp[1] + '\n'
			vcm_cfg_file_write.write(new_line)
		
		elif line.startswith("bind s1-mme"):
			s1c_cidr = str(configurations['networks']['s1c-cidr'])
			s1c_cidr = s1c_cidr.split("/")
			mme_ip = get_port_ip("s1c_to_rif1", neutron)
			new_line = "bind s1-mme ipv4-address " + mme_ip + " mask " + s1c_cidr[1] + " interface eth1\n"
			vcm_cfg_file_write.write(new_line)
			s1_ip_file.write(new_line)
		
		elif line.startswith("gtpu bind s1u-sgw"):
			assigned_ip = get_IP_from_file('s1')
			assigned_ip = assigned_ip.replace('\n', '')
			new_line = "gtpu bind s1u-sgw " + assigned_ip + " mask " + s1_cidr[1] + " interface eth1\n"
			vcm_cfg_file_write.write(new_line)
			s1_ip_file.write(new_line)
		
		elif line.startswith("sgi-endpoint bind"):
			sgi_cidr = str(configurations['networks']['sgi-cidr'])
			sgi_cidr = sgi_cidr.split("/")
			sgi_ip = get_IP_from_file('sgi')
			sgi_ip = sgi_ip.replace('\n', '')
			new_line = "sgi-endpoint bind " + sgi_ip + " mask " + sgi_cidr[1] + " interface eth2\n"
			vcm_cfg_file_write.write(new_line)
			sgi_ip_file.write(new_line)
		
		elif line.startswith("ethernet port 2"):
			new_line = "ethernet port 2 address " + sgi_ip +  " mask " + sgi_cidr[1] + '\n'
			vcm_cfg_file_write.write(new_line)
			sgi_ip_file.write(new_line)
		else:
			vcm_cfg_file_write.write(line)
	
	vcm_cfg_file_write.close()
	
	s1_ip_file.close()
	sgi_ip_file.close()
	
	param_file_read.close()
#=============================================================#
#-------------get assigned IP from file to update port ------#
def get_assigned_IP_from_file(f_name, error_logger):
	file_name = ''
	
	if f_name == 's1':
		file_name = 'source/vEPC_deploy/ip_files/s1_assigned_ips.txt'
	elif f_name == 'sgi':
		file_name = 'source/vEPC_deploy/ip_files/sgi_assigned_ips.txt'
	try:
		file_read = open(file_name, 'r')
	except:
		error_msg = file_name + ": File not found"
		error_logger.exception()
	
	if f_name == 's1':
		s1_mme = file_read.readline()
		s1_mme = s1_mme.split(" ")
		s1_u = file_read.readline()
		s1_u = s1_u.split(" ")
		
		return (s1_mme[3], s1_u[3])
	
	elif f_name == 'sgi':
		sgi = file_read.readline()
		sgi = sgi.split(" ")
		return sgi[2]
	file_reade.close()
#=============================================================#
#------------ vcm mme start edit based on mme ip------#
def mme_file_edit(configurations, neutron, logger):
	logger.info("editing mme file")
	file_name = 'source/vEPC_deploy/vcm-mme-start'
	file_str = open(file_name, 'r').readlines()
	file_write = open(file_name, 'w')
	
	s1_cidr = configurations['networks']['s1c-cidr']
	s1_cidr = s1_cidr.split("/")
	
	mme_ip = get_port_ip("s1c_to_rif1", neutron)
	
	for line in file_str:
		if line.startswith("ifconfig eth1:1"):
			new_line = "ifconfig eth1:1 " + mme_ip + "/" + s1_cidr[1] + " -arp\n"
			file_write.write(new_line)
		else:
			file_write.write(line)
	logger.info("Successfully edited mme file")
	file_write.close()
#=============================================================#
#--------------create EMS hosts file -----------#
def create_EMS_hostsfile(configurations, nova):

	filename = 'source/vEPC_deploy/hostnames/ems.txt'
	net_name = configurations['networks']['net-int-name']
	
	ems_name = configurations['vcm-cfg']['ems-vm-name']

	server = nova.servers.find(name=ems_name).addresses
	private_ip_string = server[net_name][0]['addr'] + "		EMS"
	public_ip_string = server[net_name][1]['addr'] + "		EMS"

	target = open(filename, 'w')
	
	str = private_ip_string + "\n"
	str += public_ip_string + "\n"
	str += "#127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4\n"
	str += "::1         localhost localhost.localdomain localhost6 localhost6.localdomain6\n"
	target.write(str)
	target.close()
#================create /etc/hosts file containing all VCM VMs info===============#
def create_host_file(instance_list, instance_list2, configurations, nova):
	
	str = ''
	net_name = configurations['networks']['net-int-name']
	
	for i in range(0, 7):
		server = nova.servers.find(name=instance_list[i].name).addresses
		str = str + server[net_name][0]['addr'] + "	" + instance_list[i].name + '\n'
		str = str + server[net_name][1]['addr'] + "	" + instance_list[i].name + '\n'
	
	for i in range(0, 7):
		server = nova.servers.find(name=instance_list2[i].name).addresses
		str = str + server[net_name][0]['addr'] + "	" + instance_list2[i].name + '\n'
		str = str + server[net_name][1]['addr'] + "	" + instance_list2[i].name + '\n'
	
	ems_name = configurations['vcm-cfg']['ems-vm-name']
	server = nova.servers.find(name=ems_name).addresses
	str = str + server[net_name][0]['addr'] + "	" + ems_name + '\n'
	str = str + server[net_name][1]['addr'] + "	" + ems_name + '\n'
	
	filename = 'source/vEPC_deploy/hostnames/hosts.txt'
	target = open(filename, 'w')
	
	target.write(str)
	target.close()
#============================================================================#

#------------------getting port ip assigned via dhcp----------#
def get_port_ip(portname, neutron):
	p=neutron.list_ports()
	for port in p['ports']:
		if (port['name']== portname):
			list=(port['fixed_ips'])
			#print list[0]['ip_address']
			return list[0]['ip_address']
	return 'port-not-found'
#-------------------------------------------------------#