import os    
import sys
import time
import readline
import json

# Paths for configuration files
FILE_PATH_MAIN = 'heat_templates/vEPC.yaml'
FILE_PATH_CDF = 'heat_templates/VCM_CDF.yaml'
FILE_PATH_CPE = 'heat_templates/VCM_CPE.yaml'
FILE_PATH_DPE = 'heat_templates/VCM_DPE.yaml'
FILE_PATH_RIF = 'heat_templates/VCM_RIF.yaml'
FILE_PATH_SDB = 'heat_templates/VCM_SDB.yaml'
FILE_PATH_UDB = 'heat_templates/VCM_UDB.yaml'
FILE_PATH_VEM = 'heat_templates/VCM_VEM.yaml'

DIR_hostnames = 'hostnames/'
DIR_ip_files = 'ip_files/'
DIR_IMG = '/root/IMGS/'
#----------------------------------------------------------------------------------#
def create_cluster(heat, cluster_name):

	try:
		file_main= open(FILE_PATH_MAIN, 'r')
		file_VEM = open(FILE_PATH_VEM, 'r')
		file_CPE = open(FILE_PATH_CPE, 'r')
		file_SDB = open(FILE_PATH_SDB, 'r')
		file_CDF = open(FILE_PATH_CDF, 'r')
		file_UDB = open(FILE_PATH_UDB, 'r')
		file_RIF = open(FILE_PATH_RIF, 'r')
		file_DPE = open(FILE_PATH_DPE, 'r')
	except:
		print "couldnt openfile"
	cluster_body={
	"stack_name":cluster_name,
	"template":file_main.read(),
	"files":{
	  "VCM_CDF.yaml":file_CDF.read(),
	  "VCM_CPE.yaml":file_CPE.read(),
	  "VCM_DPE.yaml":file_DPE.read(),
	  "VCM_RIF.yaml":file_RIF.read(),
	  "VCM_SDB.yaml":file_SDB.read(),
	  "VCM_UDB.yaml":file_UDB.read(),
	  "VCM_VEM.yaml":file_VEM.read()
	 },
	 "parameters": {
	 "image": "VCM_IMG",
	 "flavor": "m1.medium",
	 "security_group_def": "default",
	 "public_network": "net04_ext",
	 "availability_zone_1": "compute1",
	 "availability_zone_2": "compute2",
	 "private_network": "net04",
	 "index": "0",
	 "index_2": "10",
	 "sgi_net_name": "SGi-0",
	 "sgi_net_cidr": "172.16.20.0/24",
	 "sgi_net_pool_start": "172.16.20.10",
	 "sgi_net_pool_end": "172.16.20.30",
	 "s1_net_name": "S1-0",
	 "s1_net_cidr": "172.16.10.0/24",
	 "s1_net_pool_start": "172.16.10.10",
	 "s1_net_pool_end": "172.16.10.30",
	 "security_group_name": "vEPC_sec_grp"
	 }
	}
	try:  
		heat.stacks.create(**cluster_body)
	except:
		print ("There is an error creating cluster, exiting...")
		raise
		sys.exit()

def get_keystone_creds(configurations):
    d = {}
    d['username'] = configurations['os-creds']['os-user']
    d['password'] = configurations['os-creds']['os-pass']
    d['auth_url'] = configurations['os-creds']['os-authurl']
    d['tenant_name'] = configurations['os-creds']['os-tenant-name']
    return d

def get_nova_creds(configurations):
	d = {}
	d['username'] = configurations['os-creds']['os-user']
	d['password'] = configurations['os-creds']['os-pass']
	d['auth_url'] = configurations['os-creds']['os-authurl']
	d['project_id'] = configurations['os-creds']['os-tenant-name']
	d['version'] = "1.1"
	return d

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

def input_configurations(error_logger, logger):
	global DIR_ip_files
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

	FILE_PATH_range = DIR_ip_files + 'range_nexthop.txt'
	try:
		param_file_write = open(FILE_PATH_range, 'w')
	except:
		print "ip_files/range_nexthop.txt: file not found"
		error_logger.exception("ip_files/range_nexthop.txt: file not found")
		sys.exit()
	inp = file_read.readline()
	param_file_write.write(inp)
	
	inp = file_read.readline()
	param_file_write.write(inp)
	
	logger.info("writing to configuration file")
	json_file.close()
	with open('configurations.json', 'w') as outfile:
		json.dump(configurations, outfile)
	param_file_write.close()
	
	file_read.close()
#--------------------------------------------------------#
def get_instance_floatingip(heat, cluster_details, vm_name):
   output = vm_name + '_ip'
   for i in cluster_details.outputs:
     if i['output_key']== output:
        insatnce_ip= i['output_value']
   return insatnce_ip[0]

def get_instance_private_ip(heat, cluster_details, vm_name):
   output = vm_name + '_private_ip'
   for i in cluster_details.outputs:
     if i['output_key']== output:
        insatnce_ip= i['output_value']
   return insatnce_ip[0]

#--------create availaible IPs file-------#
def create_IP_file(netname, configurations, logger):
	global DIR_ip_files
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
	
	if 's1' in netname:
		FILE_PATH = DIR_ip_files + 's1_available_ips.txt'
		s1_e = configurations['networks']['s1_pool_end'].split('.')
		pool =  int(s1_e[3])
	elif 'sgi' in netname:
		FILE_PATH = DIR_ip_files + 'sgi_available_ips.txt'
		sgi_e = configurations['networks']['sgi_pool_end'].split('.')
		pool =  int(sgi_e[3])# - int(sgi_s[3])
		
	ip_list = get_available_IP(net_addr, int(subnet_mask[3]), pool)
	target = open(FILE_PATH, 'w')
	#target.truncate()
	target.write(ip_list)
	target.close()
	logger.info("done creating")
#-----------------------------------#
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

#--------------------------------------------#
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

#--------------------------------------------#

#-------------------writing IP of VCM config to separate file---------#
def write_cfg_file(cfg_file_name, configurations):
	
	global DIR_ip_files
	sgi_ip = ''
	
	s1_ip_filename =  DIR_ip_files + 's1_assigned_ips.txt'
	sgi_ip_filename = DIR_ip_files + 'sgi_assigned_ips.txt'
	
	s1_ip_file = open(s1_ip_filename, 'a')
	sgi_ip_file = open(sgi_ip_filename, 'a')
		
	param_file_read = open(DIR_ip_files + 'range_nexthop.txt', 'r')
	
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

#--------------------------------#
def get_IP_from_file(f_name):
	
	filename = ''
	
	if (f_name == 's1'):
		filename = DIR_ip_files + 's1_available_ips.txt'
	elif (f_name == 'sgi'):
		filename = DIR_ip_files + 'sgi_available_ips.txt'

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
#----------------------------------------------------------------#


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

def check_image_directory(img_name, logger_glance, error_logger):
	global DIR_IMG
	info_msg = "Checking if image " + img_name + " exists in the directory " + DIR_IMG
	logger_glance.info(info_msg)
	PATH = DIR_IMG + img_name + ".qcow2"
	if not os.path.isfile(PATH):
		error_msg = "Image file " + img_name + " does not exist in the directory vEPC/IMGS/, please download image files and copy to the directory vEPC/IMGS/ "
		print ("[" + time.strftime("%H:%M:%S")+ "] " + error_msg)
		logger_glance.error(error_msg)
		error_logger.error(error_msg)
		sys.exit()

#-----------create VCM and EMS image--------#
def create_image(glance, img_name, logger_glance, error_logger):
	global DIR_IMG
	info_msg = "Creating image " + img_name
	logger_glance.info(info_msg)
	IMAGE_PATH =  DIR_IMG + img_name + ".qcow2"
	try:
		image = glance.images.create(name=img_name,disk_format = 'qcow2', container_format = 'bare')
		image = glance.images.upload(image.id, open(IMAGE_PATH, 'rb'))
		info_msg = "Successfully Created image " + img_name
		logger_glance.info(info_msg)
	except:
		print ("[" + time.strftime("%H:%M:%S")+ "] Unable to create glance image, please check logs")
		error_msg = "Creating image " + img_name
		error_logger.exception(error_msg)
		sys.exit()


#-----------------availability_zones and aggregate_group-------------------#
def get_aggnameA():   
	return 'GroupA'
def get_aggnameB():
	return 'GroupB'

def get_avlzoneA():
	return 'compute1'
def get_avlzoneB():
	return 'compute2'

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

def create_aggregate_groups(nova, error_logger, logger_nova):
	logger_nova.info("Getting hypervisor list")
	hyper_list = nova.hypervisors.list()
	hostnA = hyper_list[0].service['host']
	hostnB = hyper_list[1].service['host']
	try:
		if not check_aggregate(nova, get_aggnameA(), logger_nova):
			logger_nova.info("Creating aggregate group A")
			agg_idA = nova.aggregates.create(get_aggnameA(), get_avlzoneA())
			logger_nova.info("Successfully created aggregate group B")
			logger_nova.info("Adding host " + hostnA + " to Aggregate Group A")
			nova.aggregates.add_host(aggregate=agg_idA, host=hostnA)
			logger_nova.info("Successfully added host " + hostnA + " to Aggregate Group A")
		else:
			id = get_aggregate_id(nova, get_aggnameA(), logger_nova)
			if not check_host_added_to_aggregate(nova, id, hostnA, logger_nova):
				logger_nova.info("Adding host " + hostnA + " to Aggregate Group A")
				#print("Compute 1 doesn't already added, trying to add...") #dont print in actual code, just for test
				nova.aggregates.add_host(aggregate=id, host=hostnA)
				logger_nova.info("Successfully added host " + hostnA + " to Aggregate Group A") 
			else:
				pass
				#check
	except:
		error_logger.exception("Unable to create Aggregate Group A")
		print("Unable to create Aggregate Group A, please check logs")
		sys.exit()
	try:
		if not check_aggregate(nova, get_aggnameB(), logger_nova):
			logger_nova.info("Creating aggregate group B")
			agg_idB = nova.aggregates.create(get_aggnameB(), get_avlzoneB())
			logger_nova.info("Successfully created aggregate group B")
			logger_nova.info("Adding host " + hostnB + " to Aggregate Group B")
			nova.aggregates.add_host(aggregate=agg_idB, host=hostnB)
			logger_nova.info("Successfully Added host " + hostnB + " to Aggregate Group B")
			
		else:
			id = get_aggregate_id(nova, get_aggnameB(), logger_nova)
			if not check_host_added_to_aggregate(nova, id, hostnB, logger_nova):
				logger_nova.info("Adding host " + hostnB + " to Aggregate Group B")
				#print("Compute 2 doesn't already added, trying to add...") #dont print in actual code, just for test
				nova.aggregates.add_host(aggregate=id, host=hostnB)
				logger_nova.info("Successfully added host " + hostnB + " to Aggregate Group B")
				#print("Successfull...") #dont print in actual code, just for test
			else:
				pass
				#check
	except:
		error_logger.exception("Unable to Create Aggregate Group B")
		print("Unable to create Aggregate Group B, please check logs")
		sys.exit()

#-----------------------------------------------------------------------#
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
		time_sleeping += 10
	print("[" + time.strftime("%H:%M:%S")+ "] " + vm_name+" booted up!")

def hostname_config(ssh, ip, vm_name, file_name, REMOTE_PATH_HOSTNAME, error_logger, logger_ssh):
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
	sftp.put(DIR_hostnames + "host_" + file_name, REMOTE_PATH_HOSTNAME)

	if(vm_name == 'VCM-EMS'):
		sftp.put(DIR_hostnames + "ems.txt", "/etc/hosts")
		print("[" + time.strftime("%H:%M:%S")+ "] Rebooting EMS to allow host-name changes to take effect")
		time.sleep(5)
		#ssh.exec_command("reboot")
	logger_ssh.info("Successfully Copied files")
	sftp.close()
	info_msg = vm_name + "Successfully configured"
	logger_ssh.info(info_msg)
	logger_ssh.info("Rebooting VM")
	ssh.exec_command("reboot")
	ssh.close()