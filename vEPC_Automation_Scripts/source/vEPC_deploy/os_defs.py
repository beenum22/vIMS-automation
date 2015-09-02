import os
import sys
import select
import time
import readline
import json
from datetime import datetime
import time
# from utils import *
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< NOVA FUNCTIONS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# ======================= DEPLOY A VCM COMPONENT INSTANCE AND ASSIGN NETWORKS AND FLOATING IP TO IT ======================#
def deploy_instance(vm_name, nova, f_path, neutron, configurations, avl_zone):
	image = nova.images.find(name=configurations['vcm-cfg']['vcm-img-name'])
	flavor = nova.flavors.find(name="m1.medium")
	# DPE = SGi, S1 --- RIF = S1
	net_id_int = get_network_id(netname=configurations['networks']['net-int-name'], neutron = neutron)
	print("[" + time.strftime("%H:%M:%S")+ "] Deploying "+vm_name+"...")
	cloud_file = open("source/vEPC_deploy/at/cloud-config/" + f_path) # portsS1 => 0 == s1_mme(1.4)[1.20], 1 == s1_u(1.5)[1.21]
	if "DPE-1" in vm_name:
		instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}, {'port-id':get_port_id('s1_u', neutron)}, {'port-id':get_port_id('sgi', neutron)}], availability_zone=avl_zone)
	elif "RIF-1" in vm_name:
		instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}, {'port-id':get_port_id('s1_mme', neutron)}], availability_zone=avl_zone)
	elif "DPE-2" in vm_name:
		instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}, {'port-id':get_port_id('s1_u2', neutron)}, {'port-id':get_port_id('sgi2', neutron)}], availability_zone=avl_zone)
	elif "RIF-2" in vm_name:
		instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}, {'port-id':get_port_id('s1_mme2', neutron)}], availability_zone=avl_zone)
	else:
		instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}], availability_zone=avl_zone)
	# Poll at 5 second intervals, until the status is no longer 'BUILD'
	status = instance.status
	while status == 'BUILD':
		time.sleep(2)
		# Retrieve the instance again so the status field updates
		instance = nova.servers.get(instance.id)
		status = instance.status
	cloud_file.close()
	print "[" + time.strftime("%H:%M:%S")+ "] Status: %s" % status
	if(status == 'ERROR'):
		print("[" + time.strftime("%H:%M:%S")+ "] Error occurred while deploying VM please check Openstack setup")
		sys.exit()
	while True:
		try:
			return associate_ip(vm_name = vm_name, nova = nova, net_ext=configurations['networks']['net-ext-name'])
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] Floating IP assignment error. Retrying...")
			time.sleep(2)
#-----------------------------------------------------------------------#
# ======================= DEPLOY EMS INSTANCE AND ASSIGN NETWORK AND FLOATING IP TO IT ======================#
def deploy_EMS(ems_name, nova, neutron, configurations, avl_zone):
	image = nova.images.find(name=configurations['vcm-cfg']['ems-img-name'])
	flavor = nova.flavors.find(name="m1.large")
	# DPE = SGi, S1 --- RIF = S1
	net_id_int = get_network_id(netname=configurations['networks']['net-int-name'], neutron = neutron)
	print("[" + time.strftime("%H:%M:%S")+ "] Deploying EMS...")
	instance = nova.servers.create(name=ems_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}], availability_zone=avl_zone)
	# Poll at 5 second intervals, until the status is no longer 'BUILD'
	status = instance.status
	while status == 'BUILD':
		time.sleep(3)
		# Retrieve the instance again so the status field updates
		instance = nova.servers.get(instance.id)
		status = instance.status
	print "[" + time.strftime("%H:%M:%S")+ "] Status: %s" % status
	return associate_ip(vm_name = ems_name, nova = nova, net_ext=configurations['networks']['net-ext-name']);

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
			inp = check_input(lambda x: x in ['yes', 'no'], ''+vm_name+' must be deleted to continue deployment. Delete? <yes/no> ')
		if(inp == 'yes'):
			delete_instance(vm_name=vm_name, nova=nova)
		elif(inp == 'no'):
			print("[" + time.strftime("%H:%M:%S")+ "] Aborting deployment...")
			sys.exit()
# Check if server by the name vm_name already exists and ask for appropriate action if it does
def check_server(vm_name, nova, net_int_name, net_ext):
	server_exists = is_server_exists(vm_name, nova)
	if not server_exists:
		return 'no_ip'
	
	while server_exists:	
		inp = raw_input("[" + time.strftime("%a, %d %b %Y %H:%M:%S")+ "] "+vm_name+" already exists, do you want to redeploy it? <yes/no/abort>:")
		if inp == "yes":
			delete_instance(vm_name=vm_name, nova=nova)
			
			return 'no_ip'
		elif inp == "no":
			print("[" + time.strftime("%H:%M:%S")+ "] "+vm_name+" not redeployed. Continuing with deployment...")
			if(len(item.networks[net_int_name]) > 1):		# see if the server has a floating IP
				return item.networks[net_int_name][1]
			else:
				return associate_ip(vm_name = vm_name, nova = nova, net_ext=net_ext)
		elif inp == "abort":
			print("[" + time.strftime("%H:%M:%S")+ "] Aborting deployment...")
			sys.exit()
		else:
			print("[" + time.strftime("%H:%M:%S")+ "] Wrong input, please re-try")
			
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
def associate_ip(vm_name, nova, net_ext):
	ip_list = nova.floating_ips.list()
	instance_ip = ''
	# print ip_list
	for item in ip_list:
			if 'None' == str(item.fixed_ip):
				instance_ip = item.ip
				break
	if instance_ip is '':
		instance_ip = nova.floating_ips.create(pool=net_ext).ip
	print "[" + time.strftime("%H:%M:%S")+ "] Assigned IP: <" + instance_ip + "> to "+vm_name
	instance = nova.servers.find(name=vm_name)
	instance.add_floating_ip(instance_ip)
	return instance_ip

# Check if server hostname can be pinged
def check_ping(hostname):
    response = os.system("ping -c 1 " + hostname+" > /dev/null 2>&1")
    # and then check the response...
    if response == 0:
        pingstatus = "Network Active"
    else:
        pingstatus = "Network Error"
    return pingstatus
def check_ping_status(hostname, vm_name):
	time_sleeping = 0
	while check_ping(hostname) != 'Network Active':
		if time_sleeping > 120:
			print("[" + time.strftime("%H:%M:%S")+ "] Host unreachable, please check configuration. Exiting..")
			sys.exit()
		print("[" + time.strftime("%H:%M:%S")+ "] " + vm_name + " booting up, please wait...")
		time.sleep(5)
		time_sleeping += 5
	print("[" + time.strftime("%H:%M:%S")+ "] " + vm_name+" booted up!")

def hostname_config(ssh, cmp_name, ip, vm_name, file_name, REMOTE_PATH_HOSTNAME):
	print( "[" + time.strftime("%H:%M:%S")+ "] Host-name configuration for " + vm_name)
	while(True):
		try:
			ssh.connect(ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] "+vm_name + " not ready for SSH waiting...")
			time.sleep(5)
	print( "[" + time.strftime("%H:%M:%S")+ "] \t Copying host-name file..." )
	sftp = ssh.open_sftp()
	sftp.put("source/vEPC_deploy/hostnames/host_"+file_name, REMOTE_PATH_HOSTNAME)
	
	if(vm_name == 'EMS'):
		sftp.put("source/vEPC_deploy/hostnames/ems.txt", "/etc/hosts")
		print("[" + time.strftime("%H:%M:%S")+ "] Rebooting EMS to allow host-name changes to take effect")
		time.sleep(5)
		#ssh.exec_command("reboot")
	sftp.close()
	ssh.exec_command("reboot")
	ssh.close()

def vcm_start(ssh, ip, name):
	ssh.connect(ip, username='root', password='root123')
	print("[" + time.strftime("%H:%M:%S")+ "] Starting VCM services on %s..." % name)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('service opensafd start')
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
	
	neutron.delete_network(get_network_id(network_name, neutron))
	print("[" + time.strftime("%H:%M:%S")+ "] Network "+network_name+' deleted.')

# Create network network_name and assign ports to it. If it already exists ask user for appropriate action
def create_network(network_name, neutron, configurations):
	# Check if the network already exists
	network_exists = get_network_id(netname=network_name, neutron=neutron)
	if network_exists != 'net-not-found':
		inp='yes'
		if(configurations['auto-del'] == 'no'):
			inp = check_input(lambda x: x in ['yes', 'no'], 'Network '+network_name+' must be deleted it to continue. Delete? <yes/no>: ')
		if inp == 'yes':
			clear_network(network_name, neutron, configurations)
		elif inp == 'no':
			print "[" + time.strftime("%H:%M:%S")+ "] Please delete the network " +network_name+' and re-run the script'
			sys.exit()
	start_pool=''
	end_pool=''
	if(network_name == configurations['networks']['sgi-name']):
		start_pool = configurations['networks']['sgi_pool_start']
		end_pool = configurations['networks']['sgi_pool_end']
	elif (network_name == configurations['networks']['s1-name']):
		start_pool = configurations['networks']['s1_pool_start']
		end_pool = configurations['networks']['s1_pool_end']
		
	cidr = get_network_cidr(network_name, configurations)
	# try:
	body_sample = {'network': {'name': network_name,
				'admin_state_up': True}}
 
	netw = neutron.create_network(body=body_sample)
	net_dict = netw['network']
	network_id = net_dict['id']
	print("[" + time.strftime("%H:%M:%S")+ "] Network %s created for %s" % (network_id, network_name))
	
	body_create_subnet = {'subnets': [{'name':network_name,'cidr': cidr,
						'ip_version': 4, 'network_id': network_id, 'enable_dhcp':'True', 'gateway_ip': None,
						"allocation_pools": [ {
								"start": start_pool,
								"end": end_pool }]}]}
 
	subnet = neutron.create_subnet(body=body_create_subnet)
	print("[" + time.strftime("%H:%M:%S")+ "] Created subnet %s" % cidr)
	
	ports = []
	if(network_name == configurations['networks']['s1-name']):
		ports.append(add_port_to_subnet('s1_mme', network_id, subnet, neutron))
		ports.append(add_port_to_subnet('s1_u', network_id, subnet, neutron))
		ports.append(add_port_to_subnet('s1_mme2', network_id, subnet, neutron))
		ports.append(add_port_to_subnet('s1_u2', network_id, subnet, neutron))
	elif(network_name == configurations['networks']['sgi-name']):
		ports.append(add_port_to_subnet('sgi', network_id, subnet, neutron))
		ports.append(add_port_to_subnet('sgi2', network_id, subnet, neutron))
	return ports

# Add a port to subnet
def add_port_to_subnet(name, network_id, subnet, neutron):
	body_value = {
                    "port": {
                            "admin_state_up": True,
							"name" :name,
                            "network_id": network_id
                     }
                }
	response = neutron.create_port(body=body_value)
	return response['port']['id']

#-----------#

# Get CIDR of network network_name from configurations
def get_network_cidr(network_name, configurations):
	if(network_name == configurations['networks']['sgi-name']):
		return configurations['networks']['sgi-cidr']
	elif(network_name == configurations['networks']['s1-name']):
		return configurations['networks']['s1-cidr']
	else:
		print("[" + time.strftime("%H:%M:%S")+ "] Invalid network")
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
	neutron.update_port(port_id, body=body_value)
	print("[" + time.strftime("%H:%M:%S")+ "] Port "+port_id+' for '+ port_nm +' updated...')

# ======================= GET IP ADDRESS OF A VM USING IT'S NAME ===================#
def get_IP_address(vm_name, nova, net_int_name):
	server_exists = False
	for item in nova.servers.list():
		if item.name == vm_name:
			ip = item.networks[net_int_name][0]
			#print(ip)
			server_exists = True
			return ip
			break
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< CONFIGURATION FUNCTIONS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# ======================= SOURCE THE DELL-VCM.cfg FILE ON VEM ======================#
# SEND COMMAND USING PARAMIKO CHANELL AND CHECK END PHRASE
def send_command(chan, cmd, end_phrase):
	chan.send(cmd)
	buff = ''
	while not buff.endswith(end_phrase):
		resp = chan.recv(9999)
		buff += resp
		# print buff
	print 'buff', buff
	time.sleep(2)
# MAIN FUNCTION TO SOURCE CONFIG FILE
def source_config(ssh):
	chan = ssh.invoke_shell()
	# Ssh and wait for the password prompt.
	send_command(chan, 'ssh -o StrictHostKeyChecking=no admin@localhost\n', '\'s password: ')
	# Send the password and wait for a prompt.
	send_command(chan, 'abc123\n', 'VEM-1(exec)> ')
	# Execute enable and wait for a prompt again.
	send_command(chan, 'enable\n', '(exec)# ')
	# Execute configure command and wait for a prompt again.
	send_command(chan, 'configure\n', '(configure)# ')
	# Source config file and wait for a prompt again.
	send_command(chan, 'source Dell-VCM.cfg\n', '(configure)# ')
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
	inp = raw_input(prompt +' <default: '+def_val+'>: ')
	if(inp == ''):
		return def_val
	else:
		return inp
# Main function for configuration input
def input_configurations():
	
	json_file = open('configurations.json')
	configurations = json.load(json_file)
	file_read = open('creds.txt')
	
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
	configurations['networks']['net-int-name'] = inp[1]

	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['net-ext-name'] = inp[1]

	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['s1-cidr'] = inp[1]

	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['sgi-cidr'] = inp[1]
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['s1_pool_start'] = inp[1]
	configurations['networks']['s1_pool_end'] = inp[3]
	
	inp = file_read.readline()
	inp = inp.split("\"")
	configurations['networks']['sgi_pool_start'] = inp[1]
	configurations['networks']['sgi_pool_end'] = inp[3]

	#vcm_cfg_file_read = open('range_nexthop.txt', 'r').readlines()
	param_file_write = open('source/vEPC_deploy/ip_files/range_nexthop.txt', 'w')
	
	inp = file_read.readline()
	param_file_write.write(inp)
	
	inp = file_read.readline()
	param_file_write.write(inp)
	
	json_file.close()
	with open('configurations.json', 'w') as outfile:
		json.dump(configurations, outfile)
	param_file_write.close()
	
	file_read.close()
#--------------------------------------------------------#

# Get configurations from file
def get_configurations():
	file = open('configurations.json')
	configurations = json.load(file)
	file.close()
	return configurations
#-----------------availability_zones-------------------#
def get_aggnameA():   
   return 'GroupA'
def get_aggnameB():
   return 'GroupB'

def get_avlzoneA():
   return 'compute1'
def get_avlzoneB():
   return 'compute2'

def create_agg(nova):
	hyper_list = nova.hypervisors.list()
	hostnA = hyper_list[0].service['host']
	hostnB = hyper_list[1].service['host']
	try:
	  agg_idA = nova.aggregates.create(get_aggnameA(), get_avlzoneA())
	except:
	  pass
	try:
	  agg_idB = nova.aggregates.create(get_aggnameB(), get_avlzoneB())
	except:
	  pass
	try:
	  nova.aggregates.add_host(aggregate=agg_idA, host=hostnA)
	except:
	  pass
	try:
	  nova.aggregates.add_host(aggregate=agg_idB, host=hostnB)
	except:
	  pass
#-----------------------------------------------#
#--------------create EMS hosts file -----------#
def create_EMS_hostsfile(configurations, nova):

	filename = 'source/vEPC_deploy/hostnames/ems.txt'
	net_name = configurations['networks']['net-int-name']

	server = nova.servers.find(name="EMS").addresses
	private_ip_string = server[net_name][0]['addr'] + "		EMS"
	public_ip_string = server[net_name][1]['addr'] + "		EMS"

	target = open(filename, 'w')
	
	str = private_ip_string + "\n"
	str += public_ip_string + "\n"
	str += "#127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4\n"
	str += "::1         localhost localhost.localdomain localhost6 localhost6.localdomain6\n"
	target.write(str)
	target.close()
#-------------------------------------------------------------#

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
#-----write file for s1 and sgi ip addresses assigned via dhcp------#
def ports_file_write(port_name, filename, net_cidr, neutron):
	filename = 'source/vEPC_deploy/hostnames/ifcfg-' + filename
	
	file_str = "TYPE=Ethernet\n"
	if 's1_mme' or 's1_mme2' or 's1_u' or 's1_u2' in port_name:
		file_str += "DEVICE=eth1\n"
	elif 'sgi' or 'sgi2' in port_name:
		file_str += "DEVICE=eth2\n"
	file_str += "BOOTPROTO=none\n"
	file_str += "ONBOOT=yes\n"
	file_str += "NETWORK=" + calculate_subnet_address('network_add', net_cidr) + '\n'
	file_str += "NETMASK=" + calculate_subnet_address('mask', net_cidr) + '\n'
	file_str += "IPADDR=" + get_port_ip(port_name, neutron) + '\n'
	file_str += "USERCTL=no"
	
	target = open(filename, 'w')
	target.truncate()
	target.write(file_str)
	target.close()
#-------------------------------------------------------------------#

#---------------------check if image exists-----------#
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
#------------------------------------------#
#-----------create VCM and EMS image--------#
def create_image(glance, img_name):
	
	IMAGE_PATH = "IMGS/" + img_name + ".qcow2"

	image = glance.images.create(name=img_name,disk_format = 'qcow2', container_format = 'bare')
	image = glance.images.upload(image.id, open(IMAGE_PATH, 'rb'))
	#print ('Successfully added image')
#--------------------------------------------------------#
#--------------find available IPs-----#

def get_available_IP(net_addr, mask, pool):
	
	list_ips = ''
	net_addr = net_addr.split(".")
	netw_addr = net_addr[0] + '.' + net_addr[1] + '.' + net_addr[2] + '.'
	rng = 255 - mask
	max_ip = 255 - mask - pool
	pool = pool + 1
	for i in range (pool, rng):
		ip = netw_addr + str(i)
		list_ips = list_ips + ip + '\n'
	
	return list_ips	

#-----------------------------------------#

#--------create availaible IPs file-------#
def create_IP_file(netname, configurations):
	
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
#-----------------------------------#
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
def write_cfg_file(cfg_file_name, configurations):
	ip_filename = ''
	sgi_ip = ''
	
	s1_ip_filename = 'source/vEPC_deploy/ip_files/s1_assigned_ips.txt'
	sgi_ip_filename = 'source/vEPC_deploy/ip_files/sgi_assigned_ips.txt'
	
	s1_ip_file = open(s1_ip_filename, 'a')
	sgi_ip_file = open(sgi_ip_filename, 'a')
		
	param_file_read = open('source/vEPC_deploy/ip_files/range_nexthop.txt', 'r')
	
	inp = param_file_read.readline()
	inp = inp.split("\"")
	
	vcm_cfg_file_read = open(cfg_file_name, 'r').readlines()
	vcm_cfg_file_write = open(cfg_file_name, 'w')
	
	for line in vcm_cfg_file_read:
		if line.startswith("range"):
			new_line = "range " + inp[1] + '\n'
			vcm_cfg_file_write.write(new_line)
			
		elif line.startswith("nexthop address"):
			inp = param_file_read.readline()
			inp = inp.split("\"")
			new_line = "nexthop address " + inp[1] + '\n'
			vcm_cfg_file_write.write(new_line)
		
		elif line.startswith("bind s1-mme"):
			s1_cidr = str(configurations['networks']['s1-cidr'])
			s1_cidr = s1_cidr.split("/")
			assigned_ip = get_IP_from_file('s1')
			assigned_ip = assigned_ip.replace('\n', '')
			new_line = "bind s1-mme ipv4-address " + assigned_ip + " mask " + s1_cidr[1] + " interface eth1\n"
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
#----------------------------------------------------------------#
#-------------get assigned IP from file to update port ------#
def get_assigned_IP_from_file(f_name):
	file_name = ''
	
	if f_name == 's1':
		file_name = 'source/vEPC_deploy/ip_files/s1_assigned_ips.txt'
	elif f_name == 'sgi':
		file_name = 'source/vEPC_deploy/ip_files/sgi_assigned_ips.txt'
	
	file_read = open(file_name, 'r')
	
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
#--------------------------------------------------#
#------------ vcm mme start edit based on mme ip------#
def mme_file_edit(configurations):
	
	file_name = 'source/vEPC_deploy/vcm-mme-start'
	file_str = open(file_name, 'r').readlines()
	file_write = open(file_name, 'w')
	
	s1_cidr = configurations['si-cidr']
	s1_cidr = s1_cidr.split("/")
	
	mme_ip = get_port_ip("mme", neutron)
	
	for line in file_str:
		if line.startswith("ifconfig eth1:1"):
			new_line = "ifconfig eth1:1 " + mme_ip + "/" + s1_cidr[1] + " -arp\n"
			file_write.write(new_line)
		else:
			file_write.write(line)
	
	file_write.close()
#-------------------------------------------------------#
	

