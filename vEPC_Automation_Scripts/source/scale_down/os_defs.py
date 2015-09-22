import os
import sys
import time
import readline
import json

def get_port_id_by_ip(port_ip, neutron):
	p=neutron.list_ports()
	for port in p['ports']:
		if port['fixed_ips'][0]['ip_address'] == port_ip:
			return port['id']
	return 'port-not-found'

def get_port_device_id_by_ip(port_ip, neutron):
	p=neutron.list_ports()
	for port in p['ports']:
		if port['fixed_ips'][0]['ip_address'] == port_ip:
			return port['device_id']
	return 'port-not-found'

#to check if vm instance already exist
def is_server_exists(vm_name, nova, logger_nova):
	server_exists = False
	info_msg = "Checking if " + vm_name + " already exists"
	logger_nova.info(info_msg)
	logger_nova.info("Getting nova servers list")
	for item in nova.servers.list():
		if item.name == vm_name:
			server_exists = True
			info_msg = vm_name + "already exists"
			logger_nova.info(info_msg)
			break
	if not (server_exists):
		info_msg = vm_name + "not exists"
		logger_nova.info(info_msg)	
	return server_exists

def clear_instance(vm_name, nova, configurations, neutron, logger, error_logger, logger_nova, logger_neutron):
	if is_server_exists(vm_name, nova, logger_nova):
		inp='yes'
		if(inp == 'yes'):
			delete_instance(vm_name, nova, configurations, neutron, logger, error_logger, logger_nova, logger_neutron)
			
# Delete a VM named vm_name
def delete_instance(vm_name, nova, configurations, neutron, logger, error_logger, logger_nova, logger_neutron):
	info_msg = "Terminating " + vm_name
	logger.info(info_msg)
	servers_list = nova.servers.list()
	server_del = vm_name
	server_ip = ''
	server_exists = False
	net_name = configurations['networks']['net-int-name']	
	for s in servers_list:
		if s.name == server_del:
			server_exists = True
			break
	if server_exists:
		print("[" + time.strftime("%H:%M:%S")+ "] Terminating "+vm_name+"...")
		info_msg = "Finding " + vm_name + " id"
		logger_nova.info(info_msg)
		server = nova.servers.find(name=vm_name).addresses
		try:
			server_ip = server[net_name][1]['addr']
			logger_neutron.info("Dissociating floating IP")
			floating_ip_id = get_port_device_id_by_ip(server_ip, neutron)
			neutron.delete_floatingip(floating_ip_id)
			logger_neutron.info("Successfully Dissociated floating IP")
		except:
			print "[" + time.strftime("%H:%M:%S")+ "] \tNo floating IP exists for " + vm_name	
			error_msg = " No floating IP exists for " + vm_name
			error_logger.exception(error_msg)		
		logger_nova.info("terminating instance")
		nova.servers.delete(s)
		deleted = False
		while not deleted:
			deleted = True
			for s in nova.servers.list():
				if s.name == vm_name:
					deleted = False
					continue
			time.sleep(1)
		time.sleep(2)
		logger_nova.info("Successfully terminated instance")
	else:
		info_msg = vm_name + " not found"
		logger_nova.warning()
		print("[" + time.strftime("%H:%M:%S")+ "] "+vm_name + " not found, already deleted")

def clear_network_ports(k_val, neutron, configurations, logger_neutron):
	port_nm1 = 's1_u' + str(k_val)
	port_nm2 = 'sgi' + str(k_val)
	info_msg = "Deleting network ports " + port_nm1 + "," + port_nm2
	logger_neutron.info(info_msg)
	s1_u = get_port_id(port_nm1, neutron)
	sgi = get_port_id(port_nm2, neutron)
	if(s1_u != 'port-not-found'):
		neutron.delete_port(s1_u)
		logger_neutron.info("Successfully deleted port s1_u")
		#print("[" + time.strftime("%H:%M:%S")+ "] Port s1_u deleted.")
	if(sgi != 'port-not-found'):
		neutron.delete_port(sgi)
		logger_neutron.info("Successfully deleted port sgi")
		#print("[" + time.strftime("%H:%M:%S")+ "] Port sgi deleted.")

# Fetch port ID
def get_port_id(portname, neutron):
	p=neutron.list_ports()
	for port in p['ports']:
		if (port['name']== portname):
			return port['id']
	return 'port-not-found'
#-----writing reduced k_val after scaling down---#
def input_configurations(k_val, logger):
	logger.info("Writing new scaled value to configuration file")
	file = open('configurations.json')
	configurations = json.load(file)
	
	configurations['scale-up-val'] = str(k_val)
	
	file.close()
	with open('configurations.json', 'w') as outfile:
		json.dump(configurations, outfile)
	logger.info("Successfully written new scaled value to configuration file")
# Get configurations from file
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