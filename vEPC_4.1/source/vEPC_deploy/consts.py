#!/usr/bin/env python
import os
import sys
import json
import logging
import time
#=====openstack client API imports=========#
import neutronclient.v2_0.client as ntrnclient
import glanceclient as glclient
import keystoneclient.v2_0.client as ksClient
from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient import client
#==========================================#

def keytsone_auth(name, configurations, logger, error_logger):
	keystone = ''
	logger.info("Creating authorized instance of keystone client")
	if name == 'Red Hat':
		# get credentials for keystone
		logger.info("Getting keystone credentials for authorization ...")
		credsks = get_keystone_creds(configurations)
		# get authorized instance of keystone
		logger.info("Getting authorized instance of keystone client")
		try:
			keystone = ksClient.Client(**credsks)
		except:
			error_logger.exception("Unable to create keystone client instance")
			print("[" + time.strftime("%H:%M:%S")+ "] Error creating keystone client, please check logs ...")
			sys.exit()
	elif (name == 'CentOS') or (name == 'Wind River') or (name == 'Ubuntu'):
		try:
			keystone = ksClient.Client(auth_url = configurations['os-creds']['os-authurl'],
								   username = configurations['os-creds']['os-user'],
								   password = configurations['os-creds']['os-pass'],
								   tenant_name = configurations['os-creds']['os-tenant-name'])
			
		except:
			error_logger.exception("Unable to create keyclient instance...")
			print ("[" + time.strftime("%H:%M:%S")+ "] Error creating keystone client, please check logs ...")
			sys.exit()
	logger.info("Authorized keystone instance ....")
	logger.info("Environment is " + name + " ...")
	return keystone
#========================================================#
def nova_auth(name, configurations, logger_nova, error_logger):
	nova_creds = get_nova_creds(configurations)
	nova = ''
	logger_nova.info("Creating authorized instance of nova client instance ...")
	if name == 'Red Hat':
		# get authorized instance of nova client
		logger_nova.info("Getting authorized instance to use Nova client API ...")
		try:
			auth = v2.Password(auth_url = nova_creds['auth_url'],
								username = nova_creds['username'],
								password = nova_creds['password'],
								tenant_name = nova_creds['project_id'])
			sess = session.Session(auth = auth)
			nova = client.Client(nova_creds['version'], session = sess)
		except:
			error_logger.exception("Unable to create nova client instance")
			print("[" + time.strftime("%H:%M:%S")+ "] Error authorizing nova client, please check logs ...")
			sys.exit()
	elif (name == 'CentOS') or (name == 'Wind River') or (name == 'Ubuntu'):
		try:			
			nova = client.Client('1.1', configurations['os-creds']['os-user'], 
								configurations['os-creds']['os-pass'], configurations['os-creds']['os-tenant-name'], 
								configurations['os-creds']['os-authurl'])
			
		except:
			error_logger.exception("Unable to create nova client instance ...")
			print ("[" + time.strftime("%H:%M:%S")+ "] Error authorizing nova client, please check logs ...")
			sys.exit()
	logger_nova.info("Authorized nova instance ....")
	logger_nova.info("Environment is " + name + " ...")
	return nova
#=========================================================#
def neutron_auth(name, configurations, logger_neutron, error_logger):
	credsks = get_keystone_creds(configurations)
	neutron = ''
	logger_neutron.info("Creating authorized instance of neutron client instance ...")
	if name == 'Red Hat':
		# get authorized instance of neutron client
		logger_neutron.info("Getting authorized instance of neutron client")
		try:
			neutron = ntrnclient.Client(**credsks)
		except:
			error_logger.exception("Unable to create neutron client instance")
			print("[" + time.strftime("%H:%M:%S")+ "] Error authorizing neutron client API, please check logs ...")
			sys.exit()
	elif (name == 'CentOS') or (name == 'Wind River') or (name == 'Ubuntu'):
		try:
			neutron = ntrnclient.Client(auth_url = configurations['os-creds']['os-authurl'],
								   username = configurations['os-creds']['os-user'],
								   password = configurations['os-creds']['os-pass'],
								   tenant_name = configurations['os-creds']['os-tenant-name'],
								   region_name = configurations['os-creds']['os-region-name'])
		except:
			error_logger.exception("Unable to create neutron client instance")
			print ("[" + time.strftime("%H:%M:%S")+ "] Error creating neutron client, please check logs ...")
			sys.exit()
	logger_neutron.info("Authorized neutron instance ....")
	logger_neutron.info("Environment is " + name + " ...")
	return neutron
#========================================================#
def glance_auth(name, configurations, keystone, logger_glance, error_logger):
	glance = ''
	logger_glance.info("Creating authorized instance of glance client instance ...")
	if name == 'Red Hat':
		#authorizing glance client
		logger_glance.info("Getting authorized instance of glance client")
		try:
			glance_endpoint = keystone.service_catalog.url_for(service_type = 'image', endpoint_type = 'publicURL')
			glance = glanceclient.Client('2', glance_endpoint, token = keystone.auth_token)
		except:
			error_logger.exception("Unable to create glance client instance")
			print("[" + time.strftime("%H:%M:%S")+ "] Error creating glance client, please check logs ...")
			sys.exit()
	elif (name == 'CentOS') or (name == 'Wind River') or (name == 'Ubuntu'):
		try:
			glance_endpoint = keystone.service_catalog.url_for(service_type = 'image', endpoint_type = 'publicURL')
			glance = glclient.Client('2', glance_endpoint, token = keystone.auth_token)
		except:
			error_logger.exception("Unable to create glance client instance")
			print ("[" + time.strftime("%H:%M:%S")+ "] Error creating glance client, please check logs ...")
			sys.exit()
	logger_glance.info("Authorized glance instance ....")
	logger_glance.info("Environment is " + name + " ...")
	return glance
#======================================================#
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