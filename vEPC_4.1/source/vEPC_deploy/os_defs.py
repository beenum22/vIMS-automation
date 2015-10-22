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
from consts import *
from file_defs import *
from funcs import *
from vcm_defs import *
#-----------------------------------------#
#-----------------------------------------#
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< NOVA FUNCTIONS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# ======================= DEPLOY A VCM COMPONENT INSTANCE AND ASSIGN NETWORKS AND FLOATING IP TO IT ======================#

def deploy_instance(vm_name, nova, f_path, neutron, configurations, avl_zone, error_logger, logger_nova, logger_neutron):
	info_msg = "Deploying "+vm_name
	logger_nova.info(info_msg)
	logger_nova.info("Finding Image for instance")
	image = nova.images.find(name=configurations['vcm-cfg']['vcm-img-name'])
	logger_nova.info("Finding flavour for instance")
	flavor = nova.flavors.find(name="m1.medium")
	# DPE = SGi, S1 --- RIF = S1
	net_id_int = get_network_id(netname=configurations['networks']['net-int-name'], neutron = neutron)
	print("[" + time.strftime("%H:%M:%S")+ "] Deploying "+vm_name+"...")
	cloud_file = open("source/vEPC_deploy/at/cloud-config/" + f_path)
	try:
		if "DPE-1" in vm_name:
			instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image,
						flavor=flavor, nics=[{'port-id':get_port_id('s1u_to_dpe1', neutron)}, 
												{'port-id':get_port_id('sgi_to_dpe1', neutron)}, 
												{'net-id':net_id_int}],
						availability_zone=avl_zone)
		elif "RIF-1" in vm_name:
			instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, 
						flavor=flavor, nics=[ {'port-id':get_port_id('s1c_to_rif1', neutron)},
						{'port-id':get_port_id('sgs_to_rif1', neutron)}, {'net-id':net_id_int},], 
						availability_zone=avl_zone)
		elif "DPE-2" in vm_name:
			instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image,
						flavor=flavor, nics=[ {'port-id':get_port_id('s1u_to_dpe2', neutron)},
										{'port-id':get_port_id('sgi_to_dpe2', neutron)}, {'net-id':net_id_int}], 
						availability_zone=avl_zone)
		elif "RIF-2" in vm_name:
			instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, 
						flavor=flavor, nics=[{'port-id':get_port_id('s1c_to_rif2', neutron)},
						{'port-id':get_port_id('sgs_to_rif2', neutron)}, {'net-id':net_id_int}], 
						availability_zone=avl_zone)
		elif "UDB-1" in vm_name:
			instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, 
						flavor=flavor, nics=[{'port-id':get_port_id('s6a_to_udb1', neutron)}, {'net-id':net_id_int}], 
						availability_zone=avl_zone)
		elif "UDB-2" in vm_name:
			instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, 
						flavor=flavor, nics=[{'port-id':get_port_id('s6a_to_udb2', neutron)}, {'net-id':net_id_int}], 
						availability_zone=avl_zone)
		elif "CDF-1" in vm_name:
			instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, 
						flavor=flavor, nics=[{'port-id':get_port_id('radius_to_cdf1', neutron)}, {'net-id':net_id_int}], 
						availability_zone=avl_zone)
		elif "CDF-2" in vm_name:
			instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, 
						flavor=flavor, nics=[{'port-id':get_port_id('radius_to_cdf2', neutron)}, {'net-id':net_id_int}], 
						availability_zone=avl_zone)
		else:
			instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, 
						flavor=flavor, nics=[{'net-id':net_id_int}], availability_zone=avl_zone)
	except:
		error_msg = "Unable to create instance " + vm_name
		error_logger.exception(error_msg)
		print("[" + time.strftime("%H:%M:%S")+ "] Error occurred while deploying VM please check logs...")
		sys.exit()
	# Poll at 5 second intervals, until the status is no longer 'BUILD'
	status = instance.status
	while status == 'BUILD':
		time.sleep(2)
		# Retrieve the instance again so the status field updates
		instance = nova.servers.get(instance.id)
		status = instance.status
	cloud_file.close()
	print "[" + time.strftime("%H:%M:%S")+ "] Status: %s" % status
	time.sleep(2)
	if(status == 'ERROR'):
		print("[" + time.strftime("%H:%M:%S")+ "] Error occurred while deploying VM please check logs...")
		error_msg = "Unable to Create instance " + vm_name
		error_logger.error(error_msg)
		fault = instance.fault
		error_logger.error(error_msg)
		error_logger.error(fault)
		sys.exit()
	net_name = configurations['networks']['net-int-name']
	server = nova.servers.find(name=vm_name).addresses
	private_ip = server[net_name][0]['addr']
	while True:
		try:
			ins_ip = associate_ip(vm_name, nova, configurations['networks']['net-ext-name'], neutron, error_logger, logger_neutron, private_ip)
			if ins_ip is not 'not-assigned': 
				return ins_ip 
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] Floating IP assignment error. Retrying...")
			error_logger.exception("Unable to assign floating ip")
			time.sleep(2)
#-----------------------------------------------------------------------#
# ======================= DEPLOY EMS INSTANCE AND ASSIGN NETWORK AND FLOATING IP TO IT ======================#
def deploy_EMS(ems_name, nova, neutron, configurations, avl_zone, error_logger, logger_neutron, logger_nova):
	
	logger_nova.info("Finding Image for instance")
	image = nova.images.find(name=configurations['vcm-cfg']['ems-img-name'])
	logger_nova.info("Finding flavour for instance")
	flavor = nova.flavors.find(name="m1.large")
	# DPE = SGi, S1 --- RIF = S1
	net_id_int = get_network_id(netname=configurations['networks']['net-int-name'], neutron = neutron)
	print("[" + time.strftime("%H:%M:%S")+ "] Deploying " + configurations['vcm-cfg']['ems-vm-name'] + "...")
	try:
		instance = nova.servers.create(name=ems_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}], availability_zone=avl_zone)
	except:
		error_msg = "Unable to create instance " + ems_name
		error_logger.exception(error_msg)
		sys.exit()
	# Poll at 5 second intervals, until the status is no longer 'BUILD'
	status = instance.status
	while status == 'BUILD':
		time.sleep(3)
		# Retrieve the instance again so the status field updates
		instance = nova.servers.get(instance.id)
		status = instance.status
	print "[" + time.strftime("%H:%M:%S")+ "] Status: %s" % status
	time.sleep(2)
	if(status == 'ERROR'):
		print("[" + time.strftime("%H:%M:%S")+ "] Error occurred while deploying EMS please check logs")
		error_msg = "Unable to creating instance " + ems_name
		error_logger.error(error_msg)
		fault = instance.fault
		error_logger.error(error_msg)
		error_logger.error(fault)
		sys.exit()
	info_msg = "Successfully deployed " + ems_name
	logger_nova.info(info_msg)
	net_name = configurations['networks']['net-int-name']
	server = nova.servers.find(name=ems_name).addresses
	private_ip = server[net_name][0]['addr']
	while True:
		try:
			return associate_ip(ems_name, nova, configurations['networks']['net-ext-name'], neutron, error_logger, logger_neutron, private_ip)
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] Floating IP assignment error. Retrying...")
			error_logger.exception("Unable to assign Floating IP")
			time.sleep(2)
	
def get_port_device_id_by_ip(port_ip, neutron):
	p=neutron.list_ports()
	for port in p['ports']:
		if port['fixed_ips'][0]['ip_address'] == port_ip:
			return port['device_id']
	return 'port-not-found'

	
def is_server_exists(vm_name, nova, logger_nova):
	server_exists = False
	for item in nova.servers.list():
		if item.name == vm_name:
			info_msg = vm_name + "already exists"
			logger_nova.warning(info_msg)
			server_exists = True
			break
	return server_exists
def clear_instance(vm_name, nova, auto_delete, logger_nova):
	if is_server_exists(vm_name, nova, logger_nova):
		inp='yes'
		if(auto_delete == 'no'):
			inp = check_input(lambda x: x in ['yes', 'no'], ''+vm_name+' must be deleted to continue deployment. Delete? <yes/no> ')
		if(inp == 'yes'):
			delete_instance(vm_name=vm_name, nova=nova)
		elif(inp == 'no'):
			print("[" + time.strftime("%H:%M:%S")+ "] Aborting deployment...")
			sys.exit()

# Delete a VM named vm_name
def delete_instance(vm_name, nova):
	servers_list = nova.servers.list()
	server_del = vm_name
	server_exists = False
	
	for s in servers_list:
	   if s.name == server_del:
	       server_exists = True
	       break
	if server_exists:
		nova.servers.delete(s)
		print("[" + time.strftime("%H:%M:%S")+ "] Terminating "+vm_name+"...")
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
	      print("[" + time.strftime("%H:%M:%S")+ "] Requested server not found")
		  
# Associate floating IP to server vm_name
def associate_ip(vm_name, nova, net_ext, neutron, error_logger, logger_neutron, private_ip):
	pool_id = get_network_id(net_ext,neutron)
	param = {'floatingip': {'floating_network_id': pool_id}}
	try:
		logger_neutron.info("Creating floating IP")
		floating_ip = neutron.create_floatingip(param)
	except:
		error_logger.exception("Unable to Create floating IP from pool")
		sys.exit()
	instance_ip = floating_ip['floatingip']['floating_ip_address']
	instance = nova.servers.find(name=vm_name)
	info_msg = "Associating floating IP " + instance_ip + " to " + vm_name
	logger_neutron.info(info_msg)
	try:
		instance.add_floating_ip(instance_ip, private_ip)
		print "[" + time.strftime("%H:%M:%S")+ "] Assigned IP: <" + instance_ip + "> to "+vm_name
	except:
		floating_ip_id = get_port_device_id_by_ip(instance_ip, neutron)
		neutron.delete_floatingip(floating_ip_id)
		error_msg = "Unable to associate floating IP to " + vm_name
		error_logger.exception(error_msg)
		return 'not-assigned'
	info_msg = "Successfully associated floating IP " + instance_ip + " to " + vm_name
	logger_neutron.info(info_msg)
	return instance_ip

# Check if server hostname can be pinged
def check_ping(hostname, logger):
    response = os.system("ping -c 1 " + hostname+" > /dev/null 2>&1")
    # and then check the response...
    if response == 0:
        pingstatus = "Network Active"
        logger.info("VM is up and running")
    else:
        pingstatus = "Network Error"
        logger.warning("Host is unreachable")
    return pingstatus
def check_ping_status(hostname, vm_name, logger):
	time_sleeping = 0
	info_msg = "Checking ping status of " + vm_name
	logger.info(info_msg)
	while check_ping(hostname, logger) != 'Network Active':
		if time_sleeping > 120:
			print("[" + time.strftime("%H:%M:%S")+ "] Host unreachable, please check configuration. Exiting..")
			logger.error("Host unreachable: exiting")
			sys.exit()
		print("[" + time.strftime("%H:%M:%S")+ "] " + vm_name + " booting up, please wait...")
		logger.info("Waiting for VM to boot up")
		time.sleep(5)
		time_sleeping += 5
	print("[" + time.strftime("%H:%M:%S")+ "] " + vm_name+" booted up!")

#================= copying hostname file in VMs =================#
def hostname_config(ssh, cmp_name, ip, vm_name, file_name, REMOTE_PATH_HOSTNAME, error_logger, logger_ssh):
	print( "[" + time.strftime("%H:%M:%S")+ "] Host-name configuration for " + vm_name)
	info_msg = "Starting Host-name configuration for " + vm_name
	logger_ssh.info(info_msg)
	while(True):
		try:
			info_msg = "Connecting to " + vm_name
			logger_ssh.info(info_msg)
			ssh.connect(ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] "+vm_name + " not ready for SSH waiting...")
			
			error_msg = vm_name + " not ready for SSH "
			logger_ssh.warning(error_msg)
			error_logger.exception(error_msg)
			time.sleep(5)
	info_msg = "Connected to " + vm_name
	logger_ssh.info(info_msg)
	print( "[" + time.strftime("%H:%M:%S")+ "] \t Copying host-name file..." )
	logger_ssh.info("Openning SFTP session")
	sftp = ssh.open_sftp()
	logger_ssh.info("Copying files")
	sftp.put("source/vEPC_deploy/hostnames/host_"+file_name, REMOTE_PATH_HOSTNAME)
	
	if(vm_name == 'EMS'):
		sftp.put("source/vEPC_deploy/hostnames/ems.txt", "/etc/hosts")
		print("[" + time.strftime("%H:%M:%S")+ "] Rebooting EMS to allow host-name changes to take effect")
	else:
		sftp.put("source/vEPC_deploy/hostnames/hosts.txt", "/etc/hosts")
	logger_ssh.info("Successfully Copied hostname files")
	sftp.close()
	info_msg = vm_name + "Successfully configured"
	logger_ssh.info(info_msg)
	logger_ssh.info("Rebooting VM")
	ssh.exec_command("reboot")
	ssh.close()
#======================================================================================#

def vcm_start(ssh, ip, name, logger_ssh):
	info_msg = "Connecting to " + name
	logger_ssh.info(info_msg)
	ssh.connect(ip, username='root', password='root123')
	logger_ssh.info("Successfully connected")
	logger_ssh.info("Starting opensafd service")
	print("[" + time.strftime("%H:%M:%S")+ "] Starting VCM services on %s..." % name)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('service opensafd start')
	logger_ssh.info("Started opensafd service")
	print("[" + time.strftime("%H:%M:%S")+ "] \t"+ssh_stdout.readlines()[0])
	ssh.close()
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< NEUTRON FUNCTIONS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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
			return port['id']
	return 'port-not-found'

# Fetch subnet ID
def get_subnet_id(subname, neutron):
	sn=neutron.list_subnets()
	for subnet in sn['subnets']:
		if (subnet['name']== subname):
			return subnet['id']
	return 'subnet-not-found'

def clear_network(network_name, neutron, configurations):
	
	if(network_name == configurations['networks']['s1c-name']):
		s1c_to_rif1 = get_port_id('s1c_to_rif1', neutron)
		s1c_to_rif2 = get_port_id('s1c_to_rif2', neutron)
		if(s1c_to_rif1 != 'port-not-found'):
			neutron.delete_port(s1c_to_rif1)
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1c_to_rif1 deleted.")
		if(s1c_to_rif2 != 'port-not-found'):
			neutron.delete_port(s1c_to_rif2)
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1c_to_rif2 deleted.")
	
	elif(network_name == configurations['networks']['s1u-name']):
		s1u_to_dpe1 = get_port_id('s1u_to_dpe1', neutron)
		s1u_to_dpe2 = get_port_id('s1u_to_dpe2', neutron)
		if(s1u_to_dpe1 != 'port-not-found'):
			neutron.delete_port(s1u_to_dpe1)
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1u_to_dpe1 deleted.")
		if(s1u_to_dpe2 != 'port-not-found'):
			neutron.delete_port(s1u_to_dpe2)
			print("[" + time.strftime("%H:%M:%S")+ "] Port s1u_to_dpe2 deleted.")
	
	elif(network_name == configurations['networks']['s6a-name']):
		s6a_to_udb1 = get_port_id('s6a_to_udb1', neutron)
		s6a_to_udb2 = get_port_id('s6a_to_udb2', neutron)
		if(s6a_to_udb1 != 'port-not-found'):
			neutron.delete_port(s6a_to_udb1)
			print("[" + time.strftime("%H:%M:%S")+ "] Port s6a_to_udb1 deleted.")
		if(s6a_to_udb2 != 'port-not-found'):
			neutron.delete_port(s6a_to_udb2)
			print("[" + time.strftime("%H:%M:%S")+ "] Port s6a_to_udb2 deleted.")
	
	elif(network_name == configurations['networks']['radius-name']):
		radius_to_cdf1 = get_port_id('radius_to_cdf1', neutron)
		radius_to_cdf2 = get_port_id('radius_to_cdf2', neutron)
		if(radius_to_cdf1 != 'port-not-found'):
			neutron.delete_port(radius_to_cdf1)
			print("[" + time.strftime("%H:%M:%S")+ "] Port radius_to_cdf1 deleted.")
		if(radius_to_cdf2 != 'port-not-found'):
			neutron.delete_port(radius_to_cdf2)
			print("[" + time.strftime("%H:%M:%S")+ "] Port radius_to_cdf2 deleted.")
	
	elif(network_name == configurations['networks']['sgs-name']):
		sgs_to_rif1 = get_port_id('sgs_to_rif1', neutron)
		sgs_to_rif2 = get_port_id('sgs_to_rif2', neutron)
		if(sgs_to_rif1 != 'port-not-found'):
			neutron.delete_port(sgs_to_rif1)
			print("[" + time.strftime("%H:%M:%S")+ "] Port sgs_to_rif1 deleted.")
		if(sgs_to_rif2 != 'port-not-found'):
			neutron.delete_port(sgs_to_rif2)
			print("[" + time.strftime("%H:%M:%S")+ "] Port sgs_to_rif2 deleted.")
	
	elif(network_name == configurations['networks']['sgi-name']):
		sgi_to_dpe1 = get_port_id('sgi_to_dpe1', neutron)
		sgi_to_dpe2 = get_port_id('sgi_to_dpe2', neutron)
		if(sgi_to_dpe1 != 'port-not-found'):
			neutron.delete_port(sgi_to_dpe1)
			print("[" + time.strftime("%H:%M:%S")+ "] Port sgi_to_dpe1 deleted.")
		if(sgi_to_dpe2 != 'port-not-found'):
			neutron.delete_port(sgi_to_dpe2)
			print("[" + time.strftime("%H:%M:%S")+ "] Port sgi_to_dpe2 deleted.")
	
	neutron.delete_network(get_network_id(network_name, neutron))
	print("[" + time.strftime("%H:%M:%S")+ "] Network "+network_name+' deleted.')

# Create network network_name and assign ports to it. If it already exists ask user for appropriate action
def create_network(network_name, cfg_name, neutron, configurations, logger_neutron):
	# Check if the network already exists
	info_msg = "Checking if network " + network_name + " already exits"
	logger_neutron.info(info_msg)
	network_exists = get_network_id(netname=network_name, neutron=neutron)
	#deleting network if already exists
	if network_exists != 'net-not-found':
		warning_msg = "Network " + network_name + " already exits..."
		logger_neutron.warning(info_msg)
		info_msg = "Deleting network " + network_name
		logger_neutron.info(info_msg)
		clear_network(network_name, neutron, configurations)
		logger_neutron.info("Deleted Network " + network_name + "...")
	start_pool=''
	end_pool=''
	info_msg = "Creating network " + network_name
	logger_neutron.info(info_msg)
	
	logger_neutron.info("Getting cidr...")
	cidr_str = cfg_name+ "-cidr"
	#cidr = get_network_cidr(network_name, configurations)
	cidr = configurations['networks'][cidr_str]
	(start_pool, end_pool) = cal_ip_pool(network_name, cidr, configurations)
	# try:
	body_sample = {'network': {'name': network_name,
				'admin_state_up': True}}
 
	netw = neutron.create_network(body=body_sample)
	net_dict = netw['network']
	network_id = net_dict['id']
	print("[" + time.strftime("%H:%M:%S")+ "] Network %s created for %s" % (network_id, network_name))
	logger_neutron.info("Successfully created network")
	#'gateway_ip': None,
	
	if (network_name == configurations['networks']['net-int-name']):	
		body_create_subnet = {'subnets': [{'name':network_name,'cidr': cidr,
							'ip_version': 4, 'network_id': network_id, 'enable_dhcp':'True',
							"allocation_pools": [ {
									"start": start_pool,
									"end": end_pool }]}]}
	else:
		body_create_subnet = {'subnets': [{'name':network_name,'cidr': cidr,
							'ip_version': 4, 'network_id': network_id, 'enable_dhcp':'True',
							"allocation_pools": [ {
									"start": start_pool,
									"end": end_pool }]}]}
 
	logger_neutron.info("Creating subnet...")
	subnet = neutron.create_subnet(body=body_create_subnet)
	print("[" + time.strftime("%H:%M:%S")+ "] Created subnet %s" % cidr)
	logger_neutron.info("Successfully created subnet")
	ports = []
	
	if (network_name == configurations['networks']['s1c-name']):
		ports.append(add_port_to_subnet('s1c_to_rif1', network_id, subnet, neutron, logger_neutron))
		ports.append(add_port_to_subnet('s1c_to_rif2', network_id, subnet, neutron, logger_neutron))
	elif(network_name == configurations['networks']['s1u-name']):
		ports.append(add_port_to_subnet('s1u_to_dpe1', network_id, subnet, neutron, logger_neutron))
		ports.append(add_port_to_subnet('s1u_to_dpe2', network_id, subnet, neutron, logger_neutron))
	elif(network_name == configurations['networks']['s6a-name']):
		ports.append(add_port_to_subnet('s6a_to_udb1', network_id, subnet, neutron, logger_neutron))
		ports.append(add_port_to_subnet('s6a_to_udb2', network_id, subnet, neutron, logger_neutron))
	elif(network_name == configurations['networks']['radius-name']):
		ports.append(add_port_to_subnet('radius_to_cdf1', network_id, subnet, neutron, logger_neutron))
		ports.append(add_port_to_subnet('radius_to_cdf2', network_id, subnet, neutron, logger_neutron))
	elif(network_name == configurations['networks']['sgs-name']):
		ports.append(add_port_to_subnet('sgs_to_rif1', network_id, subnet, neutron, logger_neutron))
		ports.append(add_port_to_subnet('sgs_to_rif2', network_id, subnet, neutron, logger_neutron))
	elif(network_name == configurations['networks']['sgi-name']):
		ports.append(add_port_to_subnet('sgi_to_dpe1', network_id, subnet, neutron, logger_neutron))
		ports.append(add_port_to_subnet('sgi_to_dpe2', network_id, subnet, neutron, logger_neutron))
	#return ports
#===========================================================================================================#

#============================Create VCM router and attach all networks to it===================#
def create_router(neutron, configurations):
	request = {'router': {'name': configurations['router']['name'],
                          'admin_state_up': True}}
	router = neutron.create_router(request)
	router_id = router['router']['id']
	router = neutron.show_router(router_id)
	
	network_id = get_network_id(configurations['networks']['net-ext-name'], neutron)	
	neutron.add_gateway_router(router_id, { 'network_id' : network_id })
	
	subnet_id = get_subnet_id(configurations['networks']['net-int-name'], neutron)
	neutron.add_interface_router(router_id, { 'subnet_id' : subnet_id} )
	
	subnet_id = get_subnet_id(configurations['networks']['s1c-name'], neutron)
	neutron.add_interface_router(router_id, { 'subnet_id' : subnet_id} )
	
	subnet_id = get_subnet_id(configurations['networks']['s1u-name'], neutron)
	neutron.add_interface_router(router_id, { 'subnet_id' : subnet_id} )
	
	subnet_id = get_subnet_id(configurations['networks']['s6a-name'], neutron)
	neutron.add_interface_router(router_id, { 'subnet_id' : subnet_id} )
	
	subnet_id = get_subnet_id(configurations['networks']['radius-name'], neutron)
	neutron.add_interface_router(router_id, { 'subnet_id' : subnet_id} )
	
	subnet_id = get_subnet_id(configurations['networks']['sgs-name'], neutron)
	neutron.add_interface_router(router_id, { 'subnet_id' : subnet_id} )
	
	subnet_id = get_subnet_id(configurations['networks']['sgi-name'], neutron)
	neutron.add_interface_router(router_id, { 'subnet_id' : subnet_id} )
	
#============================================================================#	

#==============get subnet of network==========#
def get_subnet_id(net_name, neutron):
	net_list = neutron.list_networks()
	
	for i in range (0, len(net_list['networks'])):
		if net_list['networks'][i]['name'] == net_name:
			return net_list['networks'][i]['subnets']
	
	return 'network-not-found'
#===========================================#

# ====================== Add a port to subnet =========================#
def add_port_to_subnet(name, network_id, subnet, neutron, logger_neutron):
	info_msg = "Adding port " + name + " to subnet"
	logger_neutron.info(info_msg)
	body_value = {
                    "port": {
                            "admin_state_up": True,
							"name" :name,
                            "network_id": network_id
                     }
                }
	response = neutron.create_port(body=body_value)
	logger_neutron.info("Successfully added port")
	return response['port']['id']

# =================================== #

# Get CIDR of network network_name from configurations
def get_network_cidr(network_name, configurations):
	if(network_name == configurations['networks']['sgi-name']):
		return configurations['networks']['sgi-cidr']
	elif(network_name == configurations['networks']['s1-name']):
		return configurations['networks']['s1-cidr']
	else:
		print("[" + time.strftime("%H:%M:%S")+ "] Invalid network")
# Update neutron port to allow address
def update_neutron_port(neutron, port_id, allowed_ip, port_nm, logger_neutron, error_logger):
	body_value = {
			"port": {
				"allowed_address_pairs": [
					{
						"ip_address":allowed_ip
					}
				]
				}
			}
	info_msg = "updating port " + port_id
	logger_neutron.info(info_msg)
	try:
		neutron.update_port(port_id, body=body_value)
	except:
		error_msg = "Unable to update port" + port_id
		error_logger.exception(error_msg)
	info_msg = "Successfully updated port " + port_id
	logger_neutron.info(info_msg)
	print("[" + time.strftime("%H:%M:%S")+ "] Port "+port_id+' for '+ port_nm +' updated...')

# ======================= GET IP ADDRESS OF A VM USING IT'S NAME ===================#
def get_IP_address(vm_name, nova, net_int_name):
	for item in nova.servers.list():
		if item.name == vm_name:
			ip = item.networks[net_int_name][0]
			#print(ip)
			return ip
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CONFIGURATION FUNCTIONS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# ======================= SOURCE THE DELL-VCM.cfg FILE ON VEM ======================#
# SEND COMMAND USING PARAMIKO CHANELL AND CHECK END PHRASE
def send_command(chan, cmd, end_phrase, logger_ssh):
	info_msg = "Sending command " + cmd
	logger_ssh.info(info_msg)
	chan.send(cmd)
	buff = ''
	while not buff.endswith(end_phrase):
		resp = chan.recv(9999)
		buff += resp
		# print buff
	print 'buff', buff
	info_msg = "Reponse buffer:" + buff 
	logger_ssh.info(info_msg)
	time.sleep(2)
# MAIN FUNCTION TO SOURCE CONFIG FILE
def source_config(ssh, logger_ssh):
	chan = ssh.invoke_shell()
	# Ssh and wait for the password prompt.
	send_command(chan, 'ssh -o StrictHostKeyChecking=no admin@localhost\n', '\'s password: ', logger_ssh)
	# Send the password and wait for a prompt.
	send_command(chan, 'abc123\n', 'VEM-1(exec)> ', logger_ssh)
	# Execute enable and wait for a prompt again.
	send_command(chan, 'enable\n', '(exec)# ', logger_ssh)
	# Execute configure command and wait for a prompt again.
	send_command(chan, 'configure\n', '(configure)# ', logger_ssh)
	# Source config file and wait for a prompt again.
	send_command(chan, 'source Dell-VCM.cfg\n', '(configure)# ', logger_ssh)
	'''
	print "exit config"
	# Exit configuration
	send_command(chan, 'end\n', 'VEM-2(exec)> ')
	print "exit config"
	# Exit admin mode
	send_command(chan, 'end\n', '[root@VEM-2 ~]# ')
	print "exit config"
	'''
	ssh.close()

#-----------------availability_zones and aggregate_group-------------------#
#getting names of aggregate group and avialability zones
def get_aggnameA():   
	return 'GroupA'
def get_aggnameB():
	return 'GroupB'

def get_avlzoneA():
	return 'compute1'
def get_avlzoneB():
	return 'compute2'
#check if aggregate group with the given names already exist
def check_aggregate(nova, agg_name, logger_nova):
	logger_nova.info("Checking if aggregate group " + agg_name + " already exists")
	list1 = nova.aggregates.list()
	agg_name_exist = False
	for x in list1:
		if x.name == agg_name:
			agg_name_exist = True
			logger_nova.info("Aggregate group " + agg_name + " already exists")
			return agg_name_exist
	logger_nova.info("Aggregate group " + agg_name + " does not exists")
	return agg_name_exist
#get id of aggregate group if already exist
def get_aggregate_id(nova, agg_name, logger_nova):
	logger_nova.info("getting ID of aggregate group " + agg_name)
	list1 = nova.aggregates.list()
	agg_id = 0
	agg_name_exist = False
	for x in list1:
		if x.name == agg_name:
			agg_id = x.id
			logger_nova.info("Done getting ID of aggregate group " + agg_name)
			logger_nova.info("ID of aggregate group " + agg_name + " " + str(agg_id))
			return agg_id
#check if compute node is added to aggregate group
def check_host_added_to_aggregate(nova, agg_id, hostname, logger_nova):
	host_added = False
	list1 = nova.aggregates.get_details(agg_id)
	logger_nova.info("Checking if " + hostname + " exists in aggregate group " + str(list1.name))
	
	nme = str(list1.hosts)
	logger_nova.info("Getting hosts details " + nme + " (name from aggregate group)")
	if(hostname in nme):
		host_added = True
		logger_nova.info("Done checking " + nme + " is already added to aggregate group " + str(list1.name))
		return host_added
	logger_nova.info("Done checking " + hostname + " does not exists in aggregate group " + str(list1.name))
	return host_added
#create aggregate group
def create_agg(nova, error_logger, logger_nova):
	logger_nova.info("Getting hypervisor list")
	hyper_list = nova.hypervisors.list()
	hostnA = hyper_list[0].service['host']
	hostnB = hyper_list[1].service['host']
	try:
		#create if aggregate group doesn't exist
		if not check_aggregate(nova, get_aggnameA(), logger_nova):
			logger_nova.info("Creating aggregate group A")
			agg_idA = nova.aggregates.create(get_aggnameA(), get_avlzoneA())
			logger_nova.info("Successfully created aggregate group B")
			logger_nova.info("Adding host " + hostnA + " to Aggregate Group A")
			nova.aggregates.add_host(aggregate=agg_idA, host=hostnA)
			logger_nova.info("Successfully added host " + hostnA + " to Aggregate Group A")
		else:
			#check if compute node is added to the already created agg group
			id = get_aggregate_id(nova, get_aggnameA(), logger_nova)
			if not check_host_added_to_aggregate(nova, id, hostnA, logger_nova):
				logger_nova.info("Adding host " + hostnA + " to Aggregate Group A")
				nova.aggregates.add_host(aggregate=id, host=hostnA)
				logger_nova.info("Successfully added host " + hostnA + " to Aggregate Group A") 
	except:
		error_logger.exception("Unable to create Aggregate Group A")
		print("Unable to create Aggregate Group A, please check logs...")
		sys.exit()
	try:
		#create if aggregate group doesn't exist
		if not check_aggregate(nova, get_aggnameB(), logger_nova):
			logger_nova.info("Creating aggregate group B")
			agg_idB = nova.aggregates.create(get_aggnameB(), get_avlzoneB())
			logger_nova.info("Successfully created aggregate group B")
			logger_nova.info("Adding host " + hostnB + " to Aggregate Group B")
			nova.aggregates.add_host(aggregate=agg_idB, host=hostnB)
			logger_nova.info("Successfully Added host " + hostnB + " to Aggregate Group B")
			
		else:
			#check if compute node is added to the already created agg group
			id = get_aggregate_id(nova, get_aggnameB(), logger_nova)
			if not check_host_added_to_aggregate(nova, id, hostnB, logger_nova):
				logger_nova.info("Adding host " + hostnB + " to Aggregate Group B")
				nova.aggregates.add_host(aggregate=id, host=hostnB)
				logger_nova.info("Successfully added host " + hostnB + " to Aggregate Group B")
	except:
		error_logger.exception("Unable to Create Aggregate Group B")
		print("Unable to create Aggregate Group B, please check logs...")
		sys.exit()
#-----------------------------------------------------------------------#

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

#---------------------check if image exists-----------#
def check_image_directory(img_name, logger_glance, error_logger):
	info_msg = "Checking if image " + img_name + " exists in the directory vEPC/IMGS/"
	logger_glance.info(info_msg)
	PATH = "IMGS/" + img_name + ".qcow2"
	if not os.path.isfile(PATH):
		error_msg = "Image file " + img_name + " does not exist in the directory vEPC/IMGS/, please download image files and copy to the directory vEPC/IMGS/ "
		print ("[" + time.strftime("%H:%M:%S")+ "] " + error_msg)
		logger_glance.error(error_msg)
		error_logger.error(error_msg)
		sys.exit()

def image_exists(glance, img_name, error_logger, logger_glance):
	
	img_exists = False
	info_msg = "checking if image " + img_name + " exists"
	logger_glance.info(info_msg)
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
#------------------------------------------#
#-----------create VCM and EMS image--------#
def create_image(glance, img_name, logger_glance, error_logger):
	info_msg = "Creating image " + img_name
	logger_glance.info(info_msg)
	IMAGE_PATH = "IMGS/" + img_name + ".qcow2"
	
	try:
		image = glance.images.create(name=img_name,disk_format = 'qcow2', container_format = 'bare')
		image = glance.images.upload(image.id, open(IMAGE_PATH, 'rb'))
		info_msg = "Successfully Created image " + img_name
		logger_glance.info(info_msg)
	except:
		print ("[" + time.strftime("%H:%M:%S")+ "] Unable to create glance image, please check logs")
		error_msg = "Unable to create image " + img_name
		error_logger.exception(error_msg)
		sys.exit()
	#print ('Successfully added image')

#--------------------------------------------------------#
#-----------------resource_check function--------#
def check_resource(nova, node, temp_list, logger):
	info_msg = "Checking Resources on " + node
	logger.info(info_msg)
	min_vcpus_required = 0
	min_ram_required = 0
	min_disk_required = 0
	
	if 'Compute 1' in node:
		min_vcpus_required = 18
		min_ram_required = 36
		min_disk_required = 360
	elif 'Compute 2' in node:
		min_vcpus_required = 14
		min_ram_required = 28
		min_disk_required = 280
	
	resource_check = False
	memory_true = False
	disk_true = False
	vcpu_true = False
	
	ram_gb = temp_list['free_ram_mb']/1024
	
	vcpus_available = int(temp_list['vcpus'])-int(temp_list['vcpus_used'])
	info_msg = "vCPUs available are " + str(vcpus_available)
	logger.info(info_msg)
	info_msg = "Memory available in GBs is " + str(ram_gb)
	logger.info(info_msg)
	info_msg = "Disk available in GBs is " + str(temp_list['free_disk_gb'])
	logger.info(info_msg)	
	if( vcpus_available >= min_vcpus_required):
		vcpu_true = True

	if( int(ram_gb) >= min_ram_required):
		memory_true = True

	if( int(temp_list['free_disk_gb']) >= min_disk_required):
		disk_true = True
	
	if vcpu_true:
		if memory_true:
			if disk_true:
				resource_check = True
			else:
				#print('Required disk = ' + min_disk_required + '\nAvailable disk = ' + temp_list['free_disk_gb'])
				info_msg = "Required disk = " + str(min_disk_required) + "Available disk = " + str(temp_list['free_disk_gb'])
				logger.warning(info_msg)
		else:
			#print('Memory required = ' + min_ram_required + '\nMemory available = ' + temp_list['free_ram_mb'])
			info_msg = "Memory required = " + str(min_ram_required) + "Memory available = " + str(ram_gb)
			logger.warning(info_msg)
	else:
		#print('VCPUs required = ' + vcpus_available + '\nVCPUs available = ' + temp_list['free_disk_gb'])
		info_msg = "VCPUs required = " + str(vcpus_available) + "VCPUs available = " + str(temp_list['free_disk_gb'])
		logger.warning(info_msg)
	info_msg = "Done checking Resources on " + node
	logger.info(info_msg)
	return resource_check
#----------------end resource check function------------#