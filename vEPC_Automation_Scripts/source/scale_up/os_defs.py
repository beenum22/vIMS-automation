import os
import sys
import time
import readline
import json
# from utils import *
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< NOVA FUNCTIONS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# ======================= DEPLOY A VCM COMPONENT INSTANCE AND ASSIGN NETWORKS AND FLOATING IP TO IT ======================#
def deploy_instance(k_val, vm_name, nova, f_path, neutron, configurations, avl_zone, error_logger, logger_nova, logger_neutron):
	info_msg = "Deploying " + vm_name
	logger_nova.info(info_msg)
	logger_nova.info("Finding Image for instance")
	image = nova.images.find(name=configurations['vcm-cfg']['vcm-img-name'])
	logger_nova.info("Finding flavour for instance")
	flavor = nova.flavors.find(name="m1.medium")
	# DPE = SGi, S1 --- RIF = S1
	net_id_int = get_network_id(netname=configurations['networks']['net-int-name'], neutron = neutron)
	print("[" + time.strftime("%H:%M:%S")+ "] Deploying "+vm_name+"...")
	cloud_file = open("source/scale_up/at/cloud-config/" + f_path + ".txt") # portsS1 => 0 == s1_mme(1.4)[1.20], 1 == s1_u(1.5)[1.21]
	ports = []
	try:
		if "DPE" in vm_name:
			port_name1 = 'sgi' + str(k_val)
			port_name2 = 's1_u' + str(k_val)
			ports.append(add_port_to_subnet(port_name1, get_network_id('SGi', neutron), neutron, logger_neutron))
			ports.append(add_port_to_subnet(port_name2, get_network_id('S1', neutron), neutron, logger_neutron))
			instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}, {'port-id':get_port_id(port_name2, neutron)}, {'port-id':get_port_id(port_name1, neutron)}], availability_zone=avl_zone)
		else:
			instance = nova.servers.create(name=vm_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}], availability_zone=avl_zone)
	except:
		error_msg = "Creating instance " + vm_name
		error_logger.exception(error_msg)
		print("[" + time.strftime("%H:%M:%S")+ "] Error occurred while deploying VM please see logs")
		sys.exit()
	# Poll at 5 second intervals, until the status is no longer 'BUILD'
	status = instance.status
	while status == 'BUILD':
		time.sleep(5)
		# Retrieve the instance again so the status field updates
		instance = nova.servers.get(instance.id)
		status = instance.status
	cloud_file.close()
	print "[" + time.strftime("%H:%M:%S")+ "] Status: %s" % status
	time.sleep(2)
	if(status == 'ERROR'):
		print("[" + time.strftime("%H:%M:%S")+ "] Error occurred while deploying VM please check logs")
		error_msg = "Creating instance " + vm_name
		error_logger.error(error_msg)
		fault = instance.fault
		error_logger.error(error_msg)
		error_logger.error(fault)
		sys.exit()

	info_msg = "Successfully deployed" + vm_name
	logger_nova.info(info_msg)

	while True:
		try:
			ins_ip = associate_ip(vm_name, nova, configurations['networks']['net-ext-name'], neutron, error_logger, logger_neutron)
			if ins_ip is not 'not-assigned': 
				return ins_ip 
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] Floating IP assignment error. Retrying...")
			error_logger.exception("Assigning floating ip")
			time.sleep(2)

def is_server_exists(vm_name, nova):
	server_exists = False
	for item in nova.servers.list():
		if item.name == vm_name:
			server_exists = True
			break
	return server_exists
def clear_instance(vm_name, nova, auto_delete):
	if is_server_exists(vm_name, nova):
		inp='yes'
		if(auto_delete == 'no'):
			inp = check_input(lambda x: x in ['yes', 'no'], '' +vm_name+' must be deleted to continue deployment. Delete? <yes/no> ')
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
	      print("[" + time.strftime("%H:%M:%S")+ "] Requested VM not found")
		  
# Associate floating IP to server vm_name
def get_port_device_id_by_ip(port_ip, neutron):
	p=neutron.list_ports()
	for port in p['ports']:
		if port['fixed_ips'][0]['ip_address'] == port_ip:
			return port['device_id']
	return 'port-not-found'

def associate_ip(vm_name, nova, net_ext, neutron, error_logger, logger_neutron):
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
		instance.add_floating_ip(instance_ip)
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
	
def hostname_config(ssh, cmp_name, ip, vm_name, file_name, REMOTE_PATH_HOSTNAME, error_logger, logger_ssh):
	print("[" + time.strftime("%H:%M:%S")+ "] Host-name configuration for " + vm_name)
	info_msg = "Starting Host-name configuration for " + vm_name
	logger_ssh.info(info_msg)
	while(True):
		try:
			info_msg = "Connecting to " + vm_name
			logger_ssh.info(info_msg)
			ssh.connect(ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] "+ vm_name + " not ready for SSH waiting...")
			error_msg = vm_name + " not ready for SSH"
			error_logger.exception(error_msg)
			time.sleep(5)
	
	info_msg = "Connected to " + vm_name
	logger_ssh.info(info_msg)
	print("[" + time.strftime("%H:%M:%S")+ "]\t Copying host-name file..." )
	logger_ssh.info("Openning SFTP session")
	sftp = ssh.open_sftp()
	logger_ssh.info("Copying files")
	sftp.put("source/scale_up/hostnames/host_"+file_name+".txt", REMOTE_PATH_HOSTNAME)
	sftp.close()
	logger_ssh.info("Successfully Copied files")
	info_msg = vm_name + "Successfully configured"
	logger_ssh.info(info_msg)
	logger_ssh.info("Rebooting VM")
	ssh.exec_command("reboot")
	ssh.close()

def vcm_start(ssh, ip, name, logger_ssh):
	info_msg = "Connecting to " + name
	logger_ssh.info(info_msg)
	ssh.connect(ip, username='root', password='root123')
	info_msg = "Connected to " + name
	logger_ssh.info(info_msg)
	print("[" + time.strftime("%H:%M:%S")+ "] Starting VCM services on %s..." % name)
	logger_ssh.info("Running command: service opensafd start")
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('service opensafd start')
	ssh.close()
# 	info_msg = ssh_stdout.readlines()[0]
#	logger_ssh.info(info_msg)
#	print("[" + time.strftime("%H:%M:%S")+ "] "+ssh_stdout.readlines()[0])

 
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
			#print (port['id'])
			return port['id']
	return 'port-not-found'

# Fetch subnet ID
def get_subnet_id(subname, neutron):
	sn=neutron.list_subnets()
	for subnet in sn['subnets']:
		if (subnet['name']== subname):
			return subnet['id']
	return 'subnet-not-found'

# Create network network_name and assign ports to it. If it already exists ask user for appropriate action
def check_network(network_name, neutron, error_logger, logger_neutron):
	# Check if the network already exists
	info_msg = "Checking if network " + network_name + "exits"
	logger_neutron.info(info_msg)
	network_exists = get_network_id(netname=network_name, neutron=neutron)
	#if network_exists != 'net-not-found':
		#inp='yes'
		#if(configurations['auto-del'] == 'no'):
	if network_exists == 'net-not-found':
	  logger_neutron.error("Network S1 and SGi must exist to continue")
	  error_logger.error("Network S1 and SGi must exist to continue")
	  logger_neutron.warning("Aborting deployment")
	  print("[" + time.strftime("%H:%M:%S")+ "] vEPC components are missing. Network S1 and SGi must exist to continue ...")
	  print("[" + time.strftime("%H:%M:%S")+ "] Please run vEPC Initial Deployment script and then run scale-up")
	  print("[" + time.strftime("%H:%M:%S")+ "] Aborting Deployment ...")
	  sys.exit()
	info_msg = "Network" + network_name + "already exits"
	logger_neutron.info(info_msg)
# Add a port to subnet
def add_port_to_subnet(name, network_id, neutron, logger_neutron):
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

# Get CIDR of network network_name from configurations
def get_network_cidr(network_name, configurations):
	if(network_name == configurations['networks']['sgi-name']):
		return configurations['networks']['sgi-cidr']
	elif(network_name == configurations['networks']['s1-name']):
		return configurations['networks']['s1-cidr']
	else:
		print('Invalid network')
# Update neutron port to allow address
def update_neutron_port(neutron, port_id, allowed_ip, port_nm):
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
		error_msg = "updating port" + port_id
		error_logger.exception(error_msg)
	info_msg = "Successfully updated port " + port_id
	logger_neutron.info(info_msg)
	print("[" + time.strftime("%H:%M:%S")+ "] Port "+port_id+' for '+ port_nm +' updated...')

# ======================= GET IP ADDRESS OF A VM USING IT'S NAME ===================#
def get_IP_address(vm_name, nova, net_int_name):
	server_exists = False
	for item in nova.servers.list():
		if item.name == vm_name:
			ip = item.networks[net_int_name][0]
			print(ip)
			server_exists = True
			return ip
			break
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CONFIGURATION FUNCTIONS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# ======================= PROMPT INPUT AND CREDENTIALS FUNCTIONS =====================#
def count_down(time_sleep):
	for i in range(0, time_sleep):
		sys.stdout.write('Starting deployment in '+str(time_sleep-i)+'... \r')
		sys.stdout.flush()
		time.sleep(1)
def check_input(predicate, msg, error_string="Illegal Input"):
	while True:
		result = raw_input(msg)
		if predicate(result):
			return result
		print(error_string)
# Prompt user to input value or use default value
def take_input(prompt, def_val):
	inp = raw_input(prompt +' <default:'+def_val+'>: ')
	if(inp == ''):
		return def_val
	else:
		return inp
# Main function for configuration input
def input_configurations(k_val, zone_val, error_logger, logger):
	logger.info("Opening Configurations.json")
	try:
		file = open('configurations.json')
		configurations = json.load(file)
	except:
		error_logger.exception("file not found: configurations.json")
	
	configurations['scale-up-val'] = str(k_val)	
	configurations['zone-val'] = str(zone_val)
	logger.info("Writing to Configurations.json")
	file.close()
	with open('configurations.json', 'w') as outfile:
		json.dump(configurations, outfile)
	logger.info("Successfully updated Configurations.json")
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

def create_agg(nova, error_logger):
	hyper_list = nova.hypervisors.list()
	hostnA = hyper_list[0].service['host']
	hostnB = hyper_list[1].service['host']
	try:
	  agg_idA = nova.aggregates.create(get_aggnameA(), get_avlzoneA())
	except:
	  error_logger.exception("Creating Aggregate group A")
	  pass
	try:
	  agg_idB = nova.aggregates.create(get_aggnameB(), get_avlzoneB())
	except:
	  error_logger.exception("Creating Aggregate group B")
	  pass
	try:
	  nova.aggregates.add_host(aggregate=agg_idA, host=hostnA)
	except:
	  error_logger.exception("Adding host to Aggregate group A")
	  pass
	try:
	  nova.aggregates.add_host(aggregate=agg_idB, host=hostnB)
	except:
	  error_logger.exception("Adding host to Aggregate group B")
	  pass

#-------create cloud file---------#
def create_cloud_file(f_name, f_list, logger):
	info_msg = "Creating cloud file " + f_name
	logger.info(info_msg)
	filename = 'source/scale_up/at/cloud-config/' + f_list + '.txt'
	str = "#cloud-config\n"
	str += "manage_etc_hosts: True\n"
	str += "hostname: " + f_name + '\n'
	str += "fqdn: " + f_name + ".private.xyz\n"
	
	target = open(filename, 'w')
	target.truncate()
	target.write(str)
	target.close()
	info_msg = "Successfully created cloud file " + f_name
	logger.info(info_msg)

#----------------------------------------#
#-------------create hosts file----------#
def create_hosts_file(f_name, f_list, logger):
	info_msg = "Creating host file " + f_name
	logger.info(info_msg)
	filename = 'source/scale_up/hostnames/host_' + f_list + '.txt'
	str = "NETWORKING=yes\n"
	str += "NETWORKING_IPV6=no\n"
	str += "NOZEROCONF=yes\n"
	str += "HOSTNAME=" + f_name + '\n'
	
	info_msg = "Successfully created host file " + f_name
	logger.info(info_msg)
	target = open(filename, 'w')
	target.truncate()
	target.write(str)
	target.close()
#---------------------------------------#

def check_resource(nova, node, temp_list, logger):
	info_msg = "Checking Resources on " + node
	logger.info(info_msg)
	
	min_vcpus_required = 6
	min_ram_required = 12
	min_disk_required = 120
	
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
		longer.warning(info_msg)
	info_msg = "Done checking Resources on " + node
	logger.info(info_msg)
	return resource_check
#----------------end resource check function------------#