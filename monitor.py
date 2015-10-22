import novaclient.v1_1.client as nvclient
import neutronclient.v2_0.client as ntrnclient
import sys
import os
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

##################################### File path function ###################################
import subprocess
p = subprocess.Popen(["pwd"], stdout=subprocess.PIPE , shell=True)
PATH = p.stdout.read()
PATH = PATH.rstrip('\n')

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
MIB_FILE_PATH = "/root/vIMS/PROJECT-CLEARWATER-MIB.txt"
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
#LOCAL_IP = '10.204.110.42'
############################## User Configuration Functions ##############################

def get_user_configurations():
  file = open(USER_CONFIG_PATH)
  configurations = json.load(file)
  file.close()
  return configurations

print('Getting user confiurations...')
user_config = get_user_configurations()
ext_net = user_config['networks']['external']
ext_net = str(ext_net)
domain = user_config['domain']['zone']
domain = str(domain)

print('Successfull')

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
  d['auth_url'] = configurations['os-creds']['os-authurl']
  d['project_id'] = configurations['os-creds']['os-project-id']
  return d
print('Getting credentials')  
def get_configurations():
  file = open(CONFIG_PATH)
  configurations = json.load(file)
  file.close()
  return configurations
print('Credentials Loaded')
config = get_configurations()

credsks = get_keystone_creds(config)
creds = get_nova_creds(config)
# Get authorized instance of nova client
nova = nvclient.Client(**creds) 
# Get authorized instance of neutron client
neutron = ntrnclient.Client(**credsks)

########################### Create Heat Stack from credentials of keystone #####################

cred = get_keystone_creds(config)
ks_client = Keystone_Client(**cred)
heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token, username='admin', passwork='admin')

#################################### Get Homestead IP ###########################################

def get_homestead_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='homestead_ip':
        homestead_ip= i['output_value']
   return homestead_ip[0]
homestead_ip = get_homestead_ip(heatclient , STACK_NAME)

SCALE_UP = False
################################## Get Homestead information ###################################
while True:

  #Connect to Homestead
  #k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  print ("Connecting To Homestead Node with IP " + homestead_ip)
  ssh.connect( hostname = homestead_ip , username = "root", password = "root123" )
  print ("Connected")
  stdin, stdout, stderr = ssh.exec_command("sudo -s")  
  
  
  #print('Checking MIB libraries')
  #stdin, stdout, stderr = ssh.exec_command("snmpwalk -v2c -c clearwater localhost PROJECT-CLEARWATER-MIB::dataConnection")
  #while not stdout.channel.exit_status_ready():
  #	# Only print data if there is data to read in the channel 
  #	if stdout.channel.recv_ready():
  #		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
  #		if len(rl) > 0:
  #			# Print data from stdout
  #			print stdout.channel.recv(1024),
      
  os.system('clear')
      
  stdin, stdout, stderr = ssh.exec_command("snmpwalk -v2c -c clearwater localhost PROJECT-CLEARWATER-MIB::homesteadIncomingRequestsCount.scopeCurrent5MinutePeriod ")
  mib_data = stdout.read()
  mib_data = str(mib_data)
  data = mib_data.split()
  no_of_incomming_requests =  data[3]
  
  stdin, stdout, stderr = ssh.exec_command("snmpwalk -v2c -c clearwater localhost PROJECT-CLEARWATER-MIB::homesteadRejectedOverloadCount.scopeCurrent5MinutePeriod ")
  mib_data = stdout.read()
  mib_data = str(mib_data)
  data = mib_data.split()
  no_of_rejected_requests =  data[3]
  # print("*************************")
  # print ("Domain = " + domain)
  # print ("Bono IP = " + bono_ip)
  # print ("Homestead IP = " + homestead_ip)
  # print ("Homer IP = " + homer_ip)
  # print("*************************")
  print ('**************************************************************')
  print ('Number of incomming requests in the current 5 minute period= '+ no_of_incomming_requests )
  print ('Number of incomming rejected requests in the current 5 minute period due to overload= '+ no_of_rejected_requests )
  print ('**************************************************************')
  
  if (int(no_of_incomming_requests) > int(CALL_THRESHOLD) and SCALE_UP == False):
  #   #Connect to Local Node
  #   #k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
  #   ssh = paramiko.SSHClient()
  #   ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  #   print ("Connecting To local Node with IP " + LOCAL_IP)
  #   ssh.connect( hostname = LOCAL_IP , username = "root", password = "r00tme" )
  #   print ("Connected")
  #   logger.info("scaling Up")
  #   stdin, stdout, stderr = ssh.exec_command("python /root/vIMS/Scale.py")  
  #   while not stdout.channel.exit_status_ready():
  # 	# Only print data if there is data to read in the channel 
  # 	  if stdout.channel.recv_ready():
  # 		  rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
  #  		  if len(rl) > 0:
  # 			# Print data from stdout
  # 			  print stdout.channel.recv(1024),    
    SCALE_UP = True    
  # print(int(no_of_incomming_requests))
  # print(int(CALL_THRESHOLD))  
    Scale.scale_up()
  
  
  if(int(no_of_incomming_requests) < int(CALL_LOWER_THRESHOLD) and SCALE_UP == True):
   #  #Connect to Local Node
   #  #k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
   #  ssh = paramiko.SSHClient()
   #  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   #  print ("Connecting To local Node with IP " + LOCAL_IP)
   #  ssh.connect( hostname = LOCAL_IP , username = "root", password = "r00tme" )
   #  print ("Connected")
   #  stdin, stdout, stderr = ssh.exec_command("python /root/vIMS/Scale_down.py")  
   #  while not stdout.channel.exit_status_ready():
  	# # Only print data if there is data to read in the channel 
  	#   if stdout.channel.recv_ready():
  	# 	  rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   # 		  if len(rl) > 0:
  	# 		# Print data from stdout
  	# 		  print stdout.channel.recv(1024),
    SCALE_UP = False
    Scale_down.scale_down()
    
  time.sleep(30)