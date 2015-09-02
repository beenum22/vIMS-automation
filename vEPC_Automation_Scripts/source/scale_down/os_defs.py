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
def is_server_exists(vm_name, nova):
	server_exists = False
	for item in nova.servers.list():
		if item.name == vm_name:
			server_exists = True
			break
	return server_exists

def clear_instance(vm_name, nova, configurations, neutron):
	if is_server_exists(vm_name, nova):
		inp='yes'
		if(inp == 'yes'):
			delete_instance(vm_name=vm_name, nova=nova, configurations=configurations, neutron=neutron)
			
# Delete a VM named vm_name
def delete_instance(vm_name, nova, configurations, neutron):
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
		server = nova.servers.find(name=vm_name).addresses
		try:
			server_ip = server[net_name][1]['addr']
			floating_ip_id = get_port_device_id_by_ip(server_ip, neutron)
			neutron.delete_floatingip(floating_ip_id)
		except:
			print "[" + time.strftime("%H:%M:%S")+ "] \tNo floating IP exists for " + vm_name	
		
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
	else:
		print("[" + time.strftime("%H:%M:%S")+ "] "+vm_name + " not found, already deleted")

def clear_network_ports(k_val, neutron, configurations):
	port_nm1 = 's1_u' + str(k_val)
	port_nm2 = 'sgi' + str(k_val)
	s1_u = get_port_id(port_nm1, neutron)
	sgi = get_port_id(port_nm2, neutron)
	if(s1_u != 'port-not-found'):
		neutron.delete_port(s1_u)
		#print("[" + time.strftime("%H:%M:%S")+ "] Port s1_u deleted.")
	if(sgi != 'port-not-found'):
		neutron.delete_port(sgi)
		#print("[" + time.strftime("%H:%M:%S")+ "] Port sgi deleted.")

# Fetch port ID
def get_port_id(portname, neutron):
	p=neutron.list_ports()
	for port in p['ports']:
		if (port['name']== portname):
			return port['id']
	return 'port-not-found'
#-----writing reduced k_val after scaling down---#
def input_configurations(k_val):
	
	file = open('configurations.json')
	configurations = json.load(file)
	
	configurations['scale-up-val'] = str(k_val)
	
	file.close()
	with open('configurations.json', 'w') as outfile:
		json.dump(configurations, outfile)
	
# Get configurations from file
def get_configurations():
	file = open('configurations.json')
	configurations = json.load(file)
	file.close()
	return configurations