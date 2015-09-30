import os    
import sys
import time
import readline
import json

#----------------------------------------------------------------------------------#
def create_cluster(heat, cluster_name):

	FILE_PATH_MAIN = "/root/test_scripts/heat_migration/vEPC.yaml"
	FILE_PATH_CDF = '/root/test_scripts/heat_migration/VCM_CDF.yaml'
	FILE_PATH_CPE = '/root/test_scripts/heat_migration/VCM_CPE.yaml'
	FILE_PATH_DPE = '/root/test_scripts/heat_migration/VCM_DPE.yaml'
	FILE_PATH_RIF = '/root/test_scripts/heat_migration/VCM_RIF.yaml'
	FILE_PATH_SDB = '/root/test_scripts/heat_migration/VCM_SDB.yaml'
	FILE_PATH_UDB = '/root/test_scripts/heat_migration/VCM_UDB.yaml'
	FILE_PATH_VEM = '/root/test_scripts/heat_migration/VCM_VEM.yaml'

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

	#vcm_cfg_file_read = open('range_nexthop.txt', 'r').readlines()
	try:
		param_file_write = open('source/vEPC_deploy/ip_files/range_nexthop.txt', 'w')
	except:
		print "source/vEPC_deploy/ip_files/range_nexthop.txt: file not found"
		error_logger.exception("source/vEPC_deploy/ip_files/range_nexthop.txt: file not found")
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
def get_instance_floatingip(heat, cluster_name, vm_name):
   cluster_details=heat.stacks.get(cluster_name)
   output = vm_name + '_ip'
   for i in cluster_details.outputs:
     if i['output_key']== output:
        insatnce_ip= i['output_value']
   return insatnce_ip
def get_instance_private_ip(heat, cluster_name, vm_name):
   cluster_details=heat.stacks.get(cluster_name)
   output = vm_name + '_private_ip'
   for i in cluster_details.outputs:
     if i['output_key']== output:
        insatnce_ip= i['output_value']
   return insatnce_ip
