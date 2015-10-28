import os
import sys
import time
import readline
import json

#======find port id using its IP=======#
def get_port_id_by_ip(port_ip, neutron):
	p = neutron.list_ports()
	for port in p['ports']:
		if port['fixed_ips'][0]['ip_address'] == port_ip:
			return port['id']
	return 'port-not-found'
#======================================#
#=========find device id of port using its IP==========#
def get_port_device_id_by_ip(port_ip, neutron):
	p = neutron.list_ports()
	for port in p['ports']:
		if port['fixed_ips'][0]['ip_address'] == port_ip:
			return port['device_id']
	return 'port-not-found'
#==================================#
#============= check if vm instance already exist and return true============#
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
#=========================================================#
#==========check if instance exists and delete it ========#
def clear_instance(vm_name, nova, auto_delete, configurations, 
					neutron, logger, error_logger, logger_nova, logger_neutron):
	
	if is_server_exists(vm_name, nova, logger_nova):
		delete_instance(vm_name, nova, configurations, neutron, 
						logger, error_logger, logger_nova, logger_neutron)
#========================================#
#===========Delete a VM named vm_name and remove floating IP==========#
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
		print("[" + time.strftime("%H:%M:%S") + "] Terminating " + vm_name + "...")
		info_msg = "Finding " + vm_name + " id"
		logger_nova.info(info_msg)
		server = nova.servers.find(name = vm_name).addresses
		try:			
			server_ip = server[net_name][1]['addr']
			logger_neutron.info("Dissociating floating IP")
			floating_ip_id = get_port_device_id_by_ip(server_ip, neutron)
			neutron.delete_floatingip(floating_ip_id)
			logger_neutron.info("Successfully Dissociated floating IP")
		except:
			print("[" + time.strftime("%H:%M:%S") + "] \tNo floating IP exists for " + vm_name)
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
		print("[" + time.strftime("%H:%M:%S") + "] " + vm_name + " not found, already deleted")
		info_msg = vm_name + " not found"
		logger_nova.warning(info_msg)
#===============================================#
# Fetch network ID of network netname
def get_network_id(netname, neutron):
	netw = neutron.list_networks()
	for net in netw['networks']:
		if(net['name'] == netname):
			# print(net['id'])
			return net['id']
	return 'net-not-found'
#============================================#
#============Fetch port ID using its name============#
def get_port_id(portname, neutron):
	p = neutron.list_ports()
	for port in p['ports']:
		if (port['name'] == portname):
			return port['id']
	return 'port-not-found'
#================================#
#================delete all networks and its ports====================#
def clear_network(network_name, neutron, configurations, 
					error_logger, logger_neutron):
	
	if(network_name == configurations['networks']['s1c-name']):
		s1c_to_rif1 = get_port_id('s1c_to_rif1', neutron)
		s1c_to_rif2 = get_port_id('s1c_to_rif2', neutron)
		if(s1c_to_rif1 != 'port-not-found'):
			neutron.delete_port(s1c_to_rif1)
			#print("[" + time.strftime("%H:%M:%S") + "] Port s1c_to_rif1 deleted.")
		if(s1c_to_rif2 != 'port-not-found'):
			neutron.delete_port(s1c_to_rif2)
			#print("[" + time.strftime("%H:%M:%S") + "] Port s1c_to_rif2 deleted.")
	
	elif(network_name == configurations['networks']['s1u-name']):
		s1u_to_dpe1 = get_port_id('s1u_to_dpe1', neutron)
		s1u_to_dpe2 = get_port_id('s1u_to_dpe2', neutron)
		if(s1u_to_dpe1 != 'port-not-found'):
			neutron.delete_port(s1u_to_dpe1)
			#print("[" + time.strftime("%H:%M:%S") + "] Port s1u_to_dpe1 deleted.")
		if(s1u_to_dpe2 != 'port-not-found'):
			neutron.delete_port(s1u_to_dpe2)
			#print("[" + time.strftime("%H:%M:%S") + "] Port s1u_to_dpe2 deleted.")
	
	elif(network_name == configurations['networks']['s6a-name']):
		s6a_to_udb1 = get_port_id('s6a_to_udb1', neutron)
		s6a_to_udb2 = get_port_id('s6a_to_udb2', neutron)
		if(s6a_to_udb1 != 'port-not-found'):
			neutron.delete_port(s6a_to_udb1)
			#print("[" + time.strftime("%H:%M:%S") + "] Port s6a_to_udb1 deleted.")
		if(s6a_to_udb2 != 'port-not-found'):
			neutron.delete_port(s6a_to_udb2)
			#print("[" + time.strftime("%H:%M:%S") + "] Port s6a_to_udb2 deleted.")
	
	elif(network_name == configurations['networks']['radius-name']):
		radius_to_cdf1 = get_port_id('radius_to_cdf1', neutron)
		radius_to_cdf2 = get_port_id('radius_to_cdf2', neutron)
		if(radius_to_cdf1 != 'port-not-found'):
			neutron.delete_port(radius_to_cdf1)
			#print("[" + time.strftime("%H:%M:%S") + "] Port radius_to_cdf1 deleted.")
		if(radius_to_cdf2 != 'port-not-found'):
			neutron.delete_port(radius_to_cdf2)
			#print("[" + time.strftime("%H:%M:%S") + "] Port radius_to_cdf2 deleted.")
	
	elif(network_name == configurations['networks']['sgs-name']):
		sgs_to_rif1 = get_port_id('sgs_to_rif1', neutron)
		sgs_to_rif2 = get_port_id('sgs_to_rif2', neutron)
		if(sgs_to_rif1 != 'port-not-found'):
			neutron.delete_port(sgs_to_rif1)
			#print("[" + time.strftime("%H:%M:%S")+ "] Port sgs_to_rif1 deleted.")
		if(sgs_to_rif2 != 'port-not-found'):
			neutron.delete_port(sgs_to_rif2)
			#print("[" + time.strftime("%H:%M:%S")+ "] Port sgs_to_rif2 deleted.")
	
	elif(network_name == configurations['networks']['sgi-name']):
		sgi_to_dpe1 = get_port_id('sgi_to_dpe1', neutron)
		sgi_to_dpe2 = get_port_id('sgi_to_dpe2', neutron)
		if(sgi_to_dpe1 != 'port-not-found'):
			neutron.delete_port(sgi_to_dpe1)
			#print("[" + time.strftime("%H:%M:%S") + "] Port sgi_to_dpe1 deleted.")
		if(sgi_to_dpe2 != 'port-not-found'):
			neutron.delete_port(sgi_to_dpe2)
			#print("[" + time.strftime("%H:%M:%S") + "] Port sgi_to_dpe2 deleted.")
	
	neutron.delete_network(get_network_id(network_name, neutron))
	print("[" + time.strftime("%H:%M:%S")+ "] Network "+network_name+' deleted.')
#===========================================================================================#
#==============delete all networks and router==================#
def del_networks(neutron, configurations, error_logger, logger_neutron):
	
	router_id = get_router_id(configurations['router']['name'], neutron)
	
	remove_interface(neutron, get_subnet_id(neutron, configurations['networks']['s1c-name']), router_id)
	clear_network(configurations['networks']['s1c-name'], neutron,
					configurations, error_logger, logger_neutron)
	
	remove_interface(neutron, get_subnet_id(neutron, configurations['networks']['s1u-name']), router_id)
	clear_network(configurations['networks']['s1u-name'], neutron, 
					configurations, error_logger, logger_neutron)
	
	remove_interface(neutron, get_subnet_id(neutron, configurations['networks']['sgs-name']), router_id)
	clear_network(configurations['networks']['sgs-name'], neutron, 
					configurations, error_logger, logger_neutron)
	
	remove_interface(neutron, get_subnet_id(neutron, configurations['networks']['sgi-name']), router_id)
	clear_network(configurations['networks']['sgi-name'], neutron, 
					configurations, error_logger, logger_neutron)
	
	remove_interface(neutron, get_subnet_id(neutron, configurations['networks']['radius-name']), router_id)
	clear_network(configurations['networks']['radius-name'], neutron, 
					configurations, error_logger, logger_neutron)
	
	remove_interface(neutron, get_subnet_id(neutron, configurations['networks']['s6a-name']), router_id)
	clear_network(configurations['networks']['s6a-name'], neutron, 
					configurations, error_logger, logger_neutron)
	
#==========================================================================================================================#
#==============get subnet of network==========#
def get_subnet_id(neutron, net_name):
	net_list = neutron.list_networks()
	id = ''
	
	for i in range (0, len(net_list['networks'])):
		if net_list['networks'][i]['name'] == net_name:
			id = net_list['networks'][i]['subnets']
			return id[0]
	
	return 'subnet-not-found'
#===========================================#
#==========Get router ID====================#
def get_router_id(router_name, neutron):
	routers_list = neutron.list_routers()
	for i in range (0, len(routers_list['routers'])):
		if (routers_list['routers'][i]['name'] == router_name):
			return routers_list['routers'][i]['id']
#===========================================#
#=============Delete Router============================#
def delete_router(neutron, router_name):
	router_id = get_router_id(router_name, neutron)
	neutron.remove_gateway_router(router_id)
	neutron.delete_router(router_id)
	print("[" + time.strftime("%H:%M:%S") + "] " + router_name + " Deleted ...")
#=======================================================#
#=======remove interfaces from router===================#
def remove_interface(neutron, subnet_id, router_id):
	neutron.remove_interface_router(router_id, { 'subnet_id' : subnet_id } )
#=======================================================#
# Get configurations from file
def get_configurations(logger, error_logger):
	try:
		logger.info("Getting configurations from file")
		file = open('configurations.json')
	except:
		print("configuration.json: file not found")
		error_logger.exception("configuration.json: file not found")
		sys.exit()
	configurations = json.load(file)
	file.close()
	return configurations
#========================================#
#======================================================#
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
#===================================================================#
#===========check if image exists=============#
def image_exists(glance, img_name, error_logger, logger_glance):
	img_exists = False
	logger_glance.info("Getting image list")
	images = glance.images.list()
	while True:
		try:
			image = images.next()
			if (img_name == image.name):
				img_exists = True
				info_msg = "Image " + img_name + " exists"
				logger_glance.info(info_msg)
				return img_exists
			#print image.name + ' - ' + image.id
		except StopIteration:
			error_logger.exception("Image not exists")
			break
	return img_exists
#============================================#
#===========delete glance images=============#
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
#==================================================#
#===========clear IP files===============#
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
	
	clear_file = file + 'S1C_assigned_ips.txt'	
	info_msg = "Deleting file " + clear_file
	logger.info(info_msg)
	file_open = open(clear_file, 'w')
	file_open.close()
	info_msg = "Successfully deleted " + clear_file
	logger.info(info_msg)
	
	clear_file = file + 'SGi_assigned_ips.txt'	
	info_msg = "Deleting file " + clear_file
	logger.info(info_msg)
	file_open = open(clear_file, 'w')
	file_open.close()
	info_msg = "Successfully deleted " + clear_file
	logger.info(info_msg)
	
	clear_file = file + 'SGi_available_ips.txt'	
	info_msg = "Deleting file " + clear_file
	logger.info(info_msg)
	file_open = open(clear_file, 'w')
	file_open.close()
	info_msg = "Successfully deleted " + clear_file
	logger.info(info_msg)
	
	clear_file = file + 'S1C_available_ips.txt'	
	info_msg = "Deleting file " + clear_file
	logger.info(info_msg)
	file_open = open(clear_file, 'w')
	file_open.close()
	info_msg = "Successfully deleted " + clear_file
	logger.info(info_msg)
	
	clear_file = file + '/range_nexthop.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	
	clear_file = file + '/VCM_Net_available_ips.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	
	clear_file = file + '/RADIUS_available_ips.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	
	clear_file = file + '/S1U_available_ips.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	
	clear_file = file + '/S6a_available_ips.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	
	clear_file = file + '/SGs_available_ips.txt'	
	file_open = open(clear_file, 'w')
	file_open.close()
	
	logger.info("Successfully deleted IP files")
#========================================================#