import os
import sys
import time
import readline
import json
# from utils import *
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< NOVA FUNCTIONS>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# ======================= DEPLOY A VCM COMPONENT INSTANCE AND ASSIGN NETWORKS AND FLOATING IP TO IT ======================#
def deploy_instance(k_val, vm_name, nova, f_path, neutron, configurations, avl_zone):
	image = nova.images.find(name=configurations['vcm-cfg']['vcm-img-name'])
	flavor = nova.flavors.find(name="m1.medium")
	# DPE = SGi, S1 --- RIF = S1
	net_id_int = get_network_id(netname=configurations['networks']['net-int-name'], neutron = neutron)
	print("[" + time.strftime("%H:%M:%S")+ "] Deploying "+vm_name+"...")
	cloud_file = open("source/scale_up/at/cloud-config/" + f_path + ".txt") # portsS1 => 0 == s1_mme(1.4)[1.20], 1 == s1_u(1.5)[1.21]
	ports = []
	if "DPE" in vm_name:
		port_name1 = 'sgi' + str(k_val)
		port_name2 = 's1_u' + str(k_val)
		ports.append(add_port_to_subnet(port_name1, get_network_id('SGi', neutron), neutron))
		ports.append(add_port_to_subnet(port_name2, get_network_id('S1', neutron), neutron))
		instance = nova.servers.create(userdata = cloud_file, name=vm_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}, {'port-id':get_port_id(port_name2, neutron)}, {'port-id':get_port_id(port_name1, neutron)}], availability_zone=avl_zone)
	else:
		instance = nova.servers.create(name=vm_name, image=image, flavor=flavor, nics=[{'net-id':net_id_int}], availability_zone=avl_zone)
	# Poll at 5 second intervals, until the status is no longer 'BUILD'
	status = instance.status
	while status == 'BUILD':
		time.sleep(5)
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
# Check if server by the name vm_name already exists and ask for appropriate action if it does
def check_server(vm_name, nova, net_int_name, net_ext):
	server_exists = is_server_exists(vm_name, nova)
	if not server_exists:
		return 'no_ip'
	
	while server_exists:	
		inp = raw_input(""+vm_name+" already exists, do you want to redeploy it? <yes/no/abort>:")
		if inp == "yes":
			delete_instance(vm_name=vm_name, nova=nova)
			
			return 'no_ip'
		elif inp == "no":
			print("[" + time.strftime("%H:%M:%S")+ "] "+vm_name+" not re-deployed. Continuing with deployment...")
			if(len(item.networks[net_int_name]) > 1):		# see if the server has a floating IP
				return item.networks[net_int_name][1]
			else:
				return associate_ip(vm_name = vm_name, nova = nova, net_ext=net_ext)
		elif inp == "abort":
			print("[" + time.strftime("%H:%M:%S")+ "] Aborting deployment...")
			sys.exit()
		else:
			print("Wrong input, please retry")
			
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
	print("[" + time.strftime("%H:%M:%S")+ "] " +vm_name+" booted up!")

def hostname_config(ssh, cmp_name, ip, vm_name, file_name, REMOTE_PATH_HOSTNAME):
	print("[" + time.strftime("%H:%M:%S")+ "] Host-name configuration for " + vm_name)
	while(True):
		try:
			ssh.connect(ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] "+ vm_name + " not ready for SSH waiting...")
			time.sleep(5)
	print("[" + time.strftime("%H:%M:%S")+ "]\t Copying host-name file..." )
	sftp = ssh.open_sftp()
	sftp.put("source/scale_up/hostnames/host_"+file_name+".txt", REMOTE_PATH_HOSTNAME)
	sftp.close()
	ssh.exec_command("reboot")
	ssh.close()

def vcm_start(ssh, ip, name):
	ssh.connect(ip, username='root', password='root123')
	print("[" + time.strftime("%H:%M:%S")+ "] Starting VCM services on %s..." % name)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('service opensafd start')
	print("[" + time.strftime("%H:%M:%S")+ "] "+ssh_stdout.readlines()[0])
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
def check_network(network_name, neutron, configurations):
	# Check if the network already exists
	network_exists = get_network_id(netname=network_name, neutron=neutron)
	#if network_exists != 'net-not-found':
		#inp='yes'
		#if(configurations['auto-del'] == 'no'):
	if network_exists == 'net-not-found':
	  print("[" + time.strftime("%H:%M:%S")+ "] vEPC components are missing. Network S1 and SGi must exist to continue ...")
	  print("[" + time.strftime("%H:%M:%S")+ "] Please run vEPC Initial Deployment script and then run scale-up")
	  print("[" + time.strftime("%H:%M:%S")+ "] Aborting Deployment ...")
	  sys.exit()

# Add a port to subnet
def add_port_to_subnet(name, network_id, neutron):
	body_value = {
                    "port": {
                            "admin_state_up": True,
							"name" :name,
                            "network_id": network_id
                     }
                }
	response = neutron.create_port(body=body_value)
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
	neutron.update_port(port_id, body=body_value)
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
def input_configurations(k_val, zone_val):
	
	file = open('configurations.json')
	configurations = json.load(file)
	
	configurations['scale-up-val'] = str(k_val)
	
	configurations['zone-val'] = str(zone_val)
	
	file.close()
	with open('configurations.json', 'w') as outfile:
		json.dump(configurations, outfile)
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

#-------create cloud file---------#
def create_cloud_file(f_name, f_list):

	filename = 'source/scale_up/at/cloud-config/' + f_list + '.txt'
	str = "#cloud-config\n"
	str += "manage_etc_hosts: True\n"
	str += "hostname: " + f_name + '\n'
	str += "fqdn: " + f_name + ".private.xyz\n"
	
	target = open(filename, 'w')
	target.truncate()
	target.write(str)
	target.close()
#----------------------------------------#
#-------------create hosts file----------#
def create_hosts_file(f_name, f_list):

	filename = 'source/scale_up/hostnames/host_' + f_list + '.txt'
	
	str = "NETWORKING=yes\n"
	str += "NETWORKING_IPV6=no\n"
	str += "NOZEROCONF=yes\n"
	str += "HOSTNAME=" + f_name + '\n'
	
	target = open(filename, 'w')
	target.truncate()
	target.write(str)
	target.close()
#---------------------------------------#
