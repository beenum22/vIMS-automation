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

def clear_instance(vm_name, nova, auto_delete, configurations, neutron, logger, error_logger, logger_nova, logger_neutron):
	if is_server_exists(vm_name, nova, logger_nova):
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
		print("[" + time.strftime("%H:%M:%S")+ "] "+vm_name + " not found, already deleted")
		info_msg = vm_name + " not found"
		logger_nova.warning(info_msg)
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

def clear_network(network_name, neutron, configurations, error_logger, logger_neutron):
	info_msg = "Deleting network" + network_name
	logger_neutron.info(info_msg)
	if(network_name == configurations['networks']['s1-name']):
		s1_mme = get_port_id('s1_mme', neutron)
		s1_u = get_port_id('s1_u', neutron)
		s1_mme2 = get_port_id('s1_mme2', neutron)
		s1_u2 = get_port_id('s1_u2', neutron)
		if(s1_mme != 'port-not-found'):
			logger_neutron.info("Deleting port s1_mme")
			neutron.delete_port(s1_mme)
			logger_neutron.info("Successfully deleted port s1_mme")
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1_mme deleted.")
		if(s1_u != 'port-not-found'):
			logger_neutron.info("Deleting port s1_u")
			neutron.delete_port(s1_u)
			logger_neutron.info("Successfully deleted port s1_u")
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1_u deleted.")
		if(s1_mme2 != 'port-not-found'):
			logger_neutron.info("Deleting port s1_mme2")
			neutron.delete_port(s1_mme2)
			logger_neutron.info("Successfully deleted port s1_mme2")
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1_mme2 deleted.")
		if(s1_u2 != 'port-not-found'):
			logger_neutron.info("Deleting port s1_u2")
			neutron.delete_port(s1_u2)
			logger_neutron.info("Successfully deleted port s1_u2")
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
		error_logger.exception("Unable to delete Network")
		pass
	
	info_msg = "Successfully deleted network" + network_name
	logger_neutron.info(info_msg)

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

def get_aggnameA():   
   return 'GroupA'
def get_aggnameB():
   return 'GroupB'

def get_avlzoneA():
   return 'compute1'
def get_avlzoneB():
   return 'compute2'

def del_agg(nova, error_logger, logger_nova):
	logger_nova.info("Deleting aggregate groups ")
	a_id = nova.aggregates.list()
	logger_nova.info("Getting hypervisor list aggregate group ")
	hyper_list = nova.hypervisors.list()
	hostnA = hyper_list[0].service['host']
	hostnB = hyper_list[1].service['host']
	try:
		logger_nova.info("Removing host A")
		nova.aggregates.remove_host(a_id[0].id, hostnA)
		logger_nova.info("Successfully removed host A ")
		logger_nova.info("Deleting aggregate group A ")
		nova.aggregates.delete(a_id[0].id)
		logger_nova.info("Successfully deleted aggregate group A ")
	except:
		error_logger.exception("Unable to Delete Aggregate group A")
		pass
	try:
		logger_nova.info("Removing host A")
		nova.aggregates.remove_host(a_id[1].id, hostnB)
		logger_nova.info("Successfully removed host B ")
		logger_nova.info("Deleting aggregate group ")
		nova.aggregates.delete(a_id[1].id)
		logger_nova.info("Successfully deleted aggregate group B ")
	except:
		error_logger.exception("Unable to Delete Aggregate group B")
		pass
	logger_nova.info("Successfully deleted aggregate groups ")
#---------------------------------------#
#----check if image exists-----#
def image_exists(glance, img_name, error_logger, logger_glance):
	img_exists = False
	logger_glance.info("Getting image list")
	images = glance.images.list()
	while True:
		try:
			image = images.next()
			if (img_name == image.name):
				img_exists = True
				info_msg = "Image " + img_name + "exists"
				logger_glance.info(info_msg)
				return img_exists
			#print image.name + ' - ' + image.id
		except StopIteration:
			error_logger.exception("Image not exists")
			break
	return img_exists
#---------------------------------#
#--------delete glance images------#
def del_image(glance, img_name, error_logger, logger_glance):
	info_msg = "Deleting " + img_name
	logger_glance.info(info_msg)
	images = glance.images.list()
	while True:
		try:
			image = images.next()
			if (img_name == image.name):
				glance.images.delete(image.id)
				return True
			#print image.name + ' - ' + image.id
		except StopIteration:
			error_logger.exception("Deleting Image")
			break
	info_msg = "Successfully deleted " + img_name
	logger_glance.info(info_msg)
#----------------------------------#
#----------clear IP files-----------------#
def clear_IP_files(logger):
	logger.info("Deleting IP files")
	file = 'source/vEPC_deploy/ip_files/'
	
	clear_file = file + 'range_nexthop.txt'	
	info_msg = "Deleting file " + clear_file
	logger.info(info_msg)
	file_open = open(clear_file, 'w')
	file_open.close()
	info_msg = "Successfully deleted " + clear_file
	logger.info(info_msg)
	
	clear_file = file + 's1_assigned_ips.txt'	
	info_msg = "Deleting file " + clear_file
	logger.info(info_msg)
	file_open = open(clear_file, 'w')
	file_open.close()
	info_msg = "Successfully deleted " + clear_file
	logger.info(info_msg)
	
	clear_file = file + 'sgi_assigned_ips.txt'	
	info_msg = "Deleting file " + clear_file
	logger.info(info_msg)
	file_open = open(clear_file, 'w')
	file_open.close()
	info_msg = "Successfully deleted " + clear_file
	logger.info(info_msg)
	
	clear_file = file + 'sgi_available_ips.txt'	
	info_msg = "Deleting file " + clear_file
	logger.info(info_msg)
	file_open = open(clear_file, 'w')
	file_open.close()
	info_msg = "Successfully deleted " + clear_file
	logger.info(info_msg)
	
	clear_file = file + 's1_available_ips.txt'	
	info_msg = "Deleting file " + clear_file
	logger.info(info_msg)
	file_open = open(clear_file, 'w')
	file_open.close()
	info_msg = "Successfully deleted " + clear_file
	logger.info(info_msg)
	
	logger.info("Successfully deleted IP files")


