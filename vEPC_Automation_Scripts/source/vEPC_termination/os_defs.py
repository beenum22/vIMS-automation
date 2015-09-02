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

def clear_instance(vm_name, nova, auto_delete, configurations, neutron):
	if is_server_exists(vm_name, nova):
		delete_instance(vm_name, nova, configurations, neutron)
			
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
	#neutron.delete_port(del_port)

# Fetch network ID of network netname
def get_network_id(netname, neutron):
	netw = neutron.list_networks()
	for net in netw['networks']:
		if(net['name'] == netname):
			# print(net['id'])
			return net['id']
	return 'net-not-found'
# Fetch port ID
def get_port_id(portname, neutron):
	p=neutron.list_ports()
	for port in p['ports']:
		if (port['name']== portname):
			#print (port['id'])
			return port['id']
	return 'port-not-found'

def clear_network(network_name, neutron, configurations):
	if(network_name == configurations['networks']['s1-name']):
		s1_mme = get_port_id('s1_mme', neutron)
		s1_u = get_port_id('s1_u', neutron)
		s1_mme2 = get_port_id('s1_mme2', neutron)
		s1_u2 = get_port_id('s1_u2', neutron)
		if(s1_mme != 'port-not-found'):
			neutron.delete_port(s1_mme)
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1_mme deleted.")
		if(s1_u != 'port-not-found'):
			neutron.delete_port(s1_u)
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1_u deleted.")
		if(s1_mme2 != 'port-not-found'):
			neutron.delete_port(s1_mme2)
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1_mme2 deleted.")
		if(s1_u2 != 'port-not-found'):
			neutron.delete_port(s1_u2)
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1_u2 deleted.")
	if(network_name == configurations['networks']['sgi-name']):
		sgi = get_port_id('sgi', neutron)
		sgi2 = get_port_id('sgi2', neutron)
		if(sgi != 'port-not-found'):
			neutron.delete_port(sgi)
			print("[" + time.strftime("%H:%M:%S")+ "] Port sgi deleted.")
		if(sgi2 != 'port-not-found'):
			neutron.delete_port(sgi2)
			print("[" + time.strftime("%H:%M:%S")+ "] Port sgi2 deleted.")
	try:
		neutron.delete_network(get_network_id(network_name, neutron))
		print("[" + time.strftime("%H:%M:%S")+ "] Network "+network_name+' deleted.')
	except:
		pass
	try:
		neutron.delete_network(get_network_id(network_name, neutron))
		print("[" + time.strftime("%H:%M:%S")+ "] Network "+network_name+' deleted.')
	except:
		pass

# Get configurations from file
def get_configurations():
	file = open('configurations.json')
	configurations = json.load(file)
	file.close()
	return configurations

def get_aggnameA():   
   return 'GroupA'
def get_aggnameB():
   return 'GroupB'

def get_avlzoneA():
   return 'compute1'
def get_avlzoneB():
   return 'compute2'

def del_agg(nova):
	a_id = nova.aggregates.list()
	hyper_list = nova.hypervisors.list()
	hostnA = hyper_list[0].service['host']
	hostnB = hyper_list[1].service['host']
	try:
		nova.aggregates.remove_host(a_id[0].id, hostnA)
		nova.aggregates.delete(a_id[0].id)
	except:
		pass

	try:
		nova.aggregates.remove_host(a_id[1].id, hostnB)
		nova.aggregates.delete(a_id[1].id)
	except:
		pass
#---------------------------------------#
#----check if image exists-----#
def image_exists(glance, img_name):
	
	img_exists = False
	
	images = glance.images.list()
	while True:
		try:
			image = images.next()
			if (img_name == image.name):
				img_exists = True
				return img_exists
			#print image.name + ' - ' + image.id
		except StopIteration:
			break
	return img_exists
#---------------------------------#
#--------delete glance images------#
def del_image(glance, img_name):
	
	images = glance.images.list()
	while True:
		try:
			image = images.next()
			if (img_name == image.name):
				glance.images.delete(image.id)
				return True
			#print image.name + ' - ' + image.id
		except StopIteration:
			break
#----------------------------------#
#----------clear IP files-----------------#
def clear_IP_files():
	
	file = 'source/vEPC_deploy/ip_files/'
	
	clear_file = file + 'range_nexthop.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	
	clear_file = file + 's1_assigned_ips.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	
	clear_file = file + 'sgi_assigned_ips.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	
	clear_file = file + 'sgi_available_ips.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	
	clear_file = file + 's1_available_ips.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	


