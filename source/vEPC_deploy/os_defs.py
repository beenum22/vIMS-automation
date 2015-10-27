import os    
import sys
import time
import readline
import json

# Paths for configuration files
FILE_PATH_MAIN = 'source/vEPC_deploy/heat_templates/vEPC.yaml'
FILE_PATH_CDF = 'source/vEPC_deploy/heat_templates/VCM_CDF.yaml'
FILE_PATH_CPE = 'source/vEPC_deploy/heat_templates/VCM_CPE.yaml'
FILE_PATH_DPE = 'source/vEPC_deploy/heat_templates/VCM_DPE.yaml'
FILE_PATH_RIF = 'source/vEPC_deploy/heat_templates/VCM_RIF.yaml'
FILE_PATH_SDB = 'source/vEPC_deploy/heat_templates/VCM_SDB.yaml'
FILE_PATH_UDB = 'source/vEPC_deploy/heat_templates/VCM_UDB.yaml'
FILE_PATH_VEM = 'source/vEPC_deploy/heat_templates/VCM_VEM.yaml'
FILE_PATH_network = 'source/vEPC_deploy/heat_templates/network.yaml'
FILE_PATH_router = 'source/vEPC_deploy/heat_templates/router.yaml'

DIR_hostnames = 'source/vEPC_deploy/hostnames/'
DIR_ip_files = 'ip_files/'
DIR_IMG = '/root/IMGS/'

#----------------------------------------------------------------------------------#
def create_cluster(heat, cluster_name, configurations, logger_heat, error_logger):

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
		error_logger.exception("Unable to open file")
		print ("[" + time.strftime("%H:%M:%S")+ "] Unable to open file")
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
	 "image": configurations['vcm-cfg']['vcm-img-name'],
	 "flavor": "m1.medium",
	 "public_network": configurations['networks']['net-ext-name'],
	 "availability_zone_1": get_avlzoneA(),
	 "availability_zone_2": get_avlzoneB(),
	 "index": "1",
	 "index_2": "2",
	 "security_group_name": "vEPC_sec_grp",
	 "router_name": "extrouter",
	 "S1_C_net_name": configurations['networks']['s1c-name'],
	 "S1_C_net_cidr": configurations['networks']['s1c-cidr'],
	 "S1_C_net_pool_start": configurations['networks']['s1c-pool-start'],
	 "S1_C_net_pool_end": configurations['networks']['s1c-pool-end'],
	 "S1_U_net_name": configurations['networks']['s1u-name'],
	 "S1_U_net_cidr": configurations['networks']['s1u-cidr'],
	 "S1_U_net_pool_start": configurations['networks']['s1u-pool-start'],
	 "S1_U_net_pool_end": configurations['networks']['s1u-pool-end'],
	 "S6a_net_name": configurations['networks']['s6a-name'],
	 "S6a_net_cidr": configurations['networks']['s6a-cidr'],
	 "S6a_net_pool_start": configurations['networks']['s6a-pool-start'],
	 "S6a_net_pool_end": configurations['networks']['s6a-pool-end'],
	 "RADIUS_net_name": configurations['networks']['radius-name'],
	 "RADIUS_net_cidr": configurations['networks']['radius-cidr'],
	 "RADIUS_net_pool_start": configurations['networks']['radius-pool-start'],
	 "RADIUS_net_pool_end": configurations['networks']['radius-pool-end'],
	 "SGs_net_name": configurations['networks']['sgs-name'],
	 "SGs_net_cidr": configurations['networks']['sgs-cidr'],
	 "SGs_net_pool_start": configurations['networks']['sgs-pool-start'],
	 "SGs_net_pool_end": configurations['networks']['sgs-pool-end'],
	 "SGi_net_name": configurations['networks']['sgi-name'],
	 "SGi_net_cidr": configurations['networks']['sgi-cidr'],
	 "SGi_net_pool_start": configurations['networks']['sgi-pool-start'],
	 "SGi_net_pool_end": configurations['networks']['sgi-pool-end'],
	 "net0_net_name": configurations['networks']['net-int-name'],
	 "net0_net_cidr": configurations['networks']['net-int-cidr'],
	 "net0_net_pool_start": configurations['networks']['net-int-pool-start'],
	 "net0_net_pool_end": configurations['networks']['net-int-pool-end'],
	 "allowed_ip_radius": configurations['networks']['allowed-ip-radius'],
	 "allowed_ip_S1U": configurations['networks']['allowed-ip-s1u'],
	 "allowed_ip_SGi": configurations['networks']['allowed-ip-sgi'],
	 "allowed_ip_S1C": configurations['networks']['allowed-ip-s1c'],
	 "allowed_ip_SGs": configurations['networks']['allowed-ip-sgs'],
	 "allowed_ip_S6a_1": configurations['networks']['allowed-ip-s6a-1'],
	 "allowed_ip_S6a_2": configurations['networks']['allowed-ip-s6a-2']
	 }
	}
	try:  
		heat.stacks.create(**cluster_body)
	except:
		error_logger.exception("Unable to create heat stack")
		print ("[" + time.strftime("%H:%M:%S")+ "] Unable to create heat stack")
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

def check_ping_status(hostname, vm_name, logger, instance_id):
	time_sleeping = 0
	info_msg = "Checking ping status of " + vm_name + "-" + str(instance_id)
	logger.info(info_msg)
	while check_ping(hostname, logger) != 'Network Active':
		if time_sleeping > 120:
			print("[" + time.strftime("%H:%M:%S")+ "] Host unreachable, please check configuration. Exiting..")
			logger.error("Host unreachable: exiting")
			sys.exit()
		print("[" + time.strftime("%H:%M:%S")+ "] " + vm_name + "-" + str(instance_id) + " booting up, please wait...")
		logger.info("Waiting for VM to boot up")
		time.sleep(5)
		time_sleeping += 5
	print("[" + time.strftime("%H:%M:%S")+ "] " + vm_name + "-" + str(instance_id) + " booted up!")

def run_deploy_script(ssh,instance_obj,logger_ssh, instance_id,error_logger):
	print("[" + time.strftime("%H:%M:%S")+ "] Running deploy_script in " + instance_obj.name + "-" + str(instance_id))
	print "\n"
	while(True):
		try:
			info_msg = "Connecting to " + instance_obj.name
			logger_ssh.info(info_msg)
			ssh.connect(instance_obj.ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] " +instance_obj.name + " not ready for SSH waiting...")
			error_msg = instance_obj.name + " not ready for SSH "
			logger_ssh.warning(error_msg)
			error_logger.exception(error_msg)
			time.sleep(10)
	
	info_msg = "Connected to " + instance_obj.name
	logger_ssh.info(info_msg)
	#print("[" + time.strftime("%H:%M:%S")+ "] \t Running deploy_script..." )
	
	if instance_obj.name == 'UDB' or instance_obj.name == 'CDF':
		internal_interface = 'eth1'
	elif instance_obj.name == 'DPE' or instance_obj.name == 'RIF':
		internal_interface = 'eth2'
	else:
		internal_interface = 'eth0'
	info_msg = "executing command: ./deploy_script --vnfc "+instance_obj.name+" --instance_id "+ str(instance_id) +" --internal_if " + internal_interface
	logger_ssh.info(info_msg)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("./deploy_script --vnfc " + instance_obj.name + " --instance_id " + str(instance_id) + " --internal_if " + internal_interface)
	ssh_stdout.readlines()
	info_msg = "executing command: ./validate_deploy.sh"
	logger_ssh.info(info_msg)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	output = ssh_stdout.readlines()
	print("[" + time.strftime("%H:%M:%S")+ "] \t"+(output[6]))
	print("[" + time.strftime("%H:%M:%S")+ "] \t"+(output[8]))
	
	ssh.close()

def start_vcm_service(ssh,instance_obj,logger_ssh,instance_id, error_logger):
	print("[" + time.strftime("%H:%M:%S")+ "] Starting VCM service in " + instance_obj.name + "-" + str(instance_id))
	print "\n"
	while(True):
		try:
			info_msg = "Connecting to " + instance_obj.name
			logger_ssh.info(info_msg)
			ssh.connect(instance_obj.ip, username='root', password='root123')
			break
		except:
			print("[" + time.strftime("%H:%M:%S")+ "] " +instance_obj.name + " not ready for SSH waiting...")
			error_msg = instance_obj.name + " not ready for SSH "
			logger_ssh.warning(error_msg)
			error_logger.exception(error_msg)
			time.sleep(10)
	
	info_msg = "Connected to " + instance_obj.name
	logger_ssh.info(info_msg)

	info_msg = "executing command: vcm-start"
	logger_ssh.info(info_msg)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("vcm-start")
	ssh_stdout.readlines()
	time.sleep(2)
	#print("[" + time.strftime("%H:%M:%S")+ "] \t"+str(ssh_stdout.readlines()))
	
	info_msg = "executing command: ./validate_deploy.sh"
	logger_ssh.info(info_msg)
	ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('./validate_deploy.sh')
	output = ssh_stdout.readlines()
	print("[" + time.strftime("%H:%M:%S")+ "] \t"+(output[10]))
	print("[" + time.strftime("%H:%M:%S")+ "] \t"+(output[13]))

	ssh.close()

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
	ssh.close()

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
	print( "[" + time.strftime("%H:%M:%S")+ "] Successfully configured, now rebooting VM " )
	ssh.exec_command("reboot")
	ssh.close()