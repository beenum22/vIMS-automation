import novaclient.v1_1.client as nvclient
import neutronclient.v2_0.client as ntrnclient
import sys
import os
from os_fun import *
from heatclient.client import Client as Heat_Client
from keystoneclient.v2_0 import Client as Keystone_Client
import glanceclient 
import keystoneclient.v2_0.client as ksClient
import json
import time
import paramiko
import select
import Scale
import Scale_down
from commands import getoutput
from multiprocessing import Process
from os import system
from time import sleep
#----------------------------------#
from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient import client
#----------------------------------#

##################################### File path function ###################################
import subprocess
p = subprocess.Popen(["pwd"], stdout=subprocess.PIPE , shell=True)
PATH = p.stdout.read()
PATH = PATH.rstrip('\n')

############################## logging #####################################################
import logging
import datetime
now = datetime.datetime.now()
date_time = now.strftime("%Y-%m-%d_%H-%M")
filename_activity = PATH+'/logs/deploy_' + date_time + '.log'
filename_error = PATH+'/logs/deploy_error_' + date_time + '.log'

logging.basicConfig(filename=filename_activity, level=logging.INFO, filemode='w', format='%(asctime)s %(levelname)-8s %(name)-23s [-]  %(message)s')

logger=logging.getLogger(__name__)
logger_nova=logging.getLogger('nova')
logger_neutron=logging.getLogger('neutron')
logger_glance = logging.getLogger('glance')
logger_ssh=logging.getLogger('paramiko')
error_logger = logging.getLogger('error_log')

# create logger with 'Error Loging'
error_logger.setLevel(logging.ERROR)
fh = logging.FileHandler(filename_error, mode = 'w')
fh.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
error_logger.addHandler(fh)
############################## Time Stamp Function ########################################
import sys
from datetime import datetime as dt

old_f = sys.stdout

class F:
    nl = True

    def write(self, x):
        if x == '\n':
            old_f.write(x)
            self.nl = True
        elif self.nl == True:
            old_f.write('%s> %s' % (str(dt.now()), x))
            self.nl = False
        else:
            old_f.write(x)

sys.stdout = F()

############################## Global Variables ##########################################
IMAGE_PATH = PATH+'/vIMS.qcow2'
COMPRESSED_FILE_PATH = '/root/IMG/vIMS-image.tar.gz'
IMAGE_DIRECTORY = '/root/IMG/'
SNMP_CONFIG_PATH = '/etc/snmp/snmpd.conf'
SNMP_FILE_PATH = PATH+'/snmpd.conf'
MIB_PATH = "/usr/share/mibs/PROJECT-CLEARWATER-MIB.txt"
#MIB_FILE_PATH = "/root/vIMS/PROJECT-CLEARWATER-MIB.txt"
MIB_FILE_PATH = "/vIMS/PROJECT-CLEARWATER-MIB.txt"
os.environ['IMAGE_PATH'] = PATH+'/IMG'
CONFIG_PATH = PATH+'/configurations.json'
USER_CONFIG_PATH = PATH+'/user_config.json'
STACK_NAME = 'IMS'
REPO_URL = 'http://repo.cw-ngv.com/stable'
ETCD_IP = ''
ELLIS_INDEX = '0'
BONO_INDEX = '0'
SPROUT_INDEX = '0'
HOMESTEAD_INDEX = '0'
HOMER_INDEX = '0'
DN_RANGE_START = '6505550000'
DN_RANGE_LENGTH = '1000'
CALL_THRESHOLD = '20000'
CALL_LOWER_THRESHOLD = '10'
STACK_HA_NAME = 'IMS-HA'
#LOCAL_IP = '10.204.110.42'
############################## User Configuration Functions ##############################

def get_user_configurations():
	file = open(USER_CONFIG_PATH)
	configurations = json.load(file)
	file.close()
	return configurations

print('Getting user confiurations...')
logger.info("Getting initial user confiurations.")
user_config = get_user_configurations()
ext_net = user_config['networks']['external']
ext_net = str(ext_net)
domain = user_config['domain']['zone']
domain = str(domain)

print('Successfull')
logger.info("Getting initial user confiurations Successfull.")
############################## Keystone Credentials Functions ############################


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
  d['api_key'] = configurations['os-creds']['os-api-key']
  d['password'] = configurations['os-creds']['os-pass']
  d['auth_url'] = configurations['os-creds']['os-authurl']
  d['project_id'] = configurations['os-creds']['os-project-id']
  d['version'] = "1.1"
  return d

print('Getting credentials')  
logger.info("Getting client credentials")
def get_configurations():
  file = open(CONFIG_PATH)
  configurations = json.load(file)
  file.close()
  return configurations
print('Credentials Loaded')
logger.info("Credentials Loaded")  
config = get_configurations()
credsks = get_keystone_creds(config)
logger.info("Getting Keystone credentials")
creds = get_nova_creds(config)
logger_nova.info("Getting of nova credentials")

# Get authorized instance of nova client
logger_nova.info("Getting authorized instance of nova client")

auth = v2.Password(auth_url=creds['auth_url'],
               username=creds['username'],
               password=creds['password'],
               tenant_name=creds['project_id'])
sess = session.Session(auth=auth)
nova = client.Client(creds['version'], session=sess)
#except:
#  error_logger.exception("Unable to create nova client instance")
#  print ("[" + time.strftime("%H:%M:%S")+ "] Error creating nova client")
#  sys.exit()
# Get authorized instance of neutron client
logger_neutron.info("Getting authorized instance of neutron client")


#nova = nvclient.Client(**creds) 
# Get authorized instance of neutron client
neutron = ntrnclient.Client(**credsks)
logger_neutron.info("Getting authorized instance of nova client")

############################## Keystone Credentials Functions ############################
cred = get_keystone_creds(config)
ks_client = Keystone_Client(**cred)
heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token, username='admin', passwork='admin')
################################# Fetch network ID of network netname ###########################

def get_network_id(netname, neutron):
	netw = neutron.list_networks()
	for net in netw['networks']:
	  if(net['name'] == netname):
	    # print(net['id'])
	    return net['id']
	return 'net-not-found'

net_id = get_network_id(netname= ext_net, neutron = neutron)
net_id = str(net_id)
private_net_id = get_network_id(netname = "IMS-private", neutron = neutron)
private_net_id = str(private_net_id)
print private_net_id
print ('Network ID of external network =' + net_id)


list = nova.hypervisors.list()
temp_list = list[0].__dict__
node = 'Compute 1'
val1 = check_resource(nova, node, temp_list)
temp_list1 = list[1].__dict__
node = 'Compute 2'
val2 = check_resource(nova, node, temp_list1)
if (val1 == True and val2 == True):
  zone = decide_zone(nova, temp_list, temp_list1)
  print('i am in decision phase')
elif (val1 == True):
  zone='Compute 1'
  print('i am in decision val1')
else :
  zone='Compute 2'
  print('i am in decision else')
print zone

