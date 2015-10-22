import os    
import sys
import time
import readline
import json

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

def delete_cluster(heat,cluster_full_name):
	try:
		heat.stacks.delete(cluster_full_name)
		print('Removing heat stack')
	except:
		print ("Unable to find Heat-stack to be deleted..")

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
def delete_image(glance, img_name, error_logger, logger_glance):
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
def get_aggnameA():   
   return 'GroupA'
def get_aggnameB():
   return 'GroupB'

def get_avlzoneA():
   return 'compute1'
def get_avlzoneB():
   return 'compute2'

def delete_aggregate_group(nova, error_logger, logger_nova):
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