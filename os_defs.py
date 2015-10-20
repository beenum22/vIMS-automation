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
FILE_PATH_network = 'heat_templates/network.yaml'
FILE_PATH_router = 'heat_templates/router.yaml'

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
		file_net = open(FILE_PATH_network, 'r')
		file_router = open(FILE_PATH_router, 'r')
	except:
		print "could not open file"
	cluster_body={
	"stack_name":cluster_name,
	"template":file_main.read(),
	"files":{
	  "network.yaml":file_net.read(),
	  "router.yaml":file_router.read(),
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
	 "public_network": "net04_ext",
	 "availability_zone_1": "compute1",
	 "availability_zone_2": "compute2",
	 "index": "1",
	 "index_2": "2",
	 "security_group_name": "vEPC_sec_grp",
	 "router_name": "extrouter",
	 "S1_C_net_name": "S1C",
	 "S1_C_net_cidr": "172.100.10.0/27",
	 "S1_C_net_pool_start": "172.100.10.2",
	 "S1_C_net_pool_end": "172.100.10.30",
	 "S1_U_net_name": "S1U",
	 "S1_U_net_cidr": "172.100.11.0/27",
	 "S1_U_net_pool_start": "172.100.11.2",
	 "S1_U_net_pool_end": "172.100.11.30",
	 "S6a_net_name": "S6a",
	 "S6a_net_cidr": "172.100.13.0/27",
	 "S6a_net_pool_start": "172.100.13.2",
	 "S6a_net_pool_end": "172.100.13.30",
	 "RADIUS_net_name": "RADIUS",
	 "RADIUS_net_cidr": "172.100.14.0/27",
	 "RADIUS_net_pool_start": "172.100.14.2",
	 "RADIUS_net_pool_end": "172.100.14.30",
	 "SGs_net_name": "SGs",
	 "SGs_net_cidr": "172.100.12.0/27",
	 "SGs_net_pool_start": "172.100.12.2",
	 "SGs_net_pool_end": "172.100.12.30",
	 "SGi_net_name": "SGi",
	 "SGi_net_cidr": "172.100.15.0/27",
	 "SGi_net_pool_start": "172.100.15.2",
	 "SGi_net_pool_end": "172.100.15.30",
	 "net0_net_name": "net0",
	 "net0_net_cidr": "10.0.0.0/24",
	 "net0_net_pool_start": "10.0.0.2",
	 "net0_net_pool_end": "10.0.0.254"
	 }
	}
	try:  
		heat.stacks.create(**cluster_body)
	except:
		print ("Unable to create stack, exiting...")
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
	logger.info("writing to configuration file")
	json_file.close()
	with open('configurations.json', 'w') as outfile:
		json.dump(configurations, outfile)
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
