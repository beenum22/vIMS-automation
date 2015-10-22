import novaclient.v1_1.client as nvclient
import neutronclient.v2_0.client as ntrnclient
import sys
import os
from heatclient.client import Client as Heat_Client
from keystoneclient.v2_0 import Client as Keystone_Client
import glanceclient 
import keystoneclient.v2_0.client as ksClient
import json
import paramiko
import select

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

################################ Global Variables ##########################################

os.environ['IMAGE_PATH'] = PATH+'/IMG'
CONFIG_PATH = PATH+'/configurations.json'
USER_CONFIG_PATH = PATH+'/user_config.json'
STACK_NAME = 'IMS'
USERS_FILE_PATH = PATH+'/users.csv'
USERS_REMOTE_PATH = '/root/users.csv'
HOMER_CONFIG_PATH = '/root/users.create_xdm.sh'

############################## Keystone Credentials Functions ##############################

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


#Create a Heat instance 

cred = get_keystone_creds(config)
ks_client = Keystone_Client(**cred)
heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token)

##################################### Get Homestead IP #########################################

def get_homestead_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='homestead_ip':
        homestead_ip= i['output_value']
   return homestead_ip[0]

##################################### Configure Homestead ######################################

#Get Homestead IP
homestead_ip = get_homestead_ip(heatclient , STACK_NAME)

#connect to homestead
#k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print "Connecting To Homestead"
ssh.connect( hostname = homestead_ip , username = "root", password = "root123" )
print "Connected"

stdin, stdout, stderr = ssh.exec_command("sudo -s")
sftp = ssh.open_sftp()
sftp.put( USERS_FILE_PATH, USERS_REMOTE_PATH)
print('Users file successfully copied')
stdin, stdout, stderr = ssh.exec_command("cd /home/ec2-user")

#Delete existing users
#print('Deleting existing users')
#stdin, stdout, stderr = ssh.exec_command("cqlsh")
#stdin, stdout, stderr = ssh.exec_command("USE homestead_provisioning;")      
#stdin, stdout, stderr = ssh.exec_command("TRUNCATE public;")
#stdin, stdout, stderr = ssh.exec_command("TRUNCATE private;")
#stdin, stdout, stderr = ssh.exec_command("TRUNCATE service_profiles;")
#stdin, stdout, stderr = ssh.exec_command("TRUNCATE implicit_registration_sets;")
#stdin, stdout, stderr = ssh.exec_command("exit")
#print ('Successfully deleted users')

print('Creating Users in Homestead')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
stdin, stdout, stderr = ssh.exec_command("chmod 755 users.csv")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
stdin, stdout, stderr = ssh.exec_command("/usr/share/clearwater/homestead/src/metaswitch/crest/tools/bulk_create.py users.csv")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
      
#Change file permissions
stdin, stdout, stderr = ssh.exec_command("chmod 755 users.create_homestead.sh")
stdin, stdout, stderr = ssh.exec_command("chmod 755 users.create_xdm.sh")
stdin, stdout, stderr = ssh.exec_command("chmod 755 users.create_xdm.cqlsh")

#Copy files to copy in homer node

sftp.get('/root/users.create_xdm.sh' , '/tmp/users.create_xdm.sh')
sftp.get('/root/users.create_xdm.cqlsh' , '/tmp/users.create_xdm.cqlsh')


stdin, stdout, stderr = ssh.exec_command("./users.create_homestead.sh")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
print('Successfully Created Users in Homestead')

sftp.close()
ssh.close()


#################################### Get Homer IP #########################################

def get_homer_ip(heat, cluster_name):
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='homer_ip':
        homer_ip= i['output_value']
   return homer_ip[0]
   
   
   
#################################### Configure Homer ######################################

#Get Homer IP
homer_ip = get_homer_ip(heatclient , STACK_NAME)

#Connect to Homer
#k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print "Connecting To Homer"
ssh.connect( hostname = homer_ip , username = "root", password = "root123")
print "Connected To Homer"

stdin, stdout, stderr = ssh.exec_command("sudo -s")
sftp = ssh.open_sftp()
sftp.put('/tmp/users.create_xdm.sh' , '/root/users.create_xdm.sh' )
sftp.put('/tmp/users.create_xdm.cqlsh' , '/root/users.create_xdm.cqlsh')
print('Users file successfully copied')

print('Creating Users in Homer')
stdin, stdout, stderr = ssh.exec_command("cd /home/ec2-user")
stdin, stdout, stderr = ssh.exec_command("chmod 755 users.create_xdm.sh")
stdin, stdout, stderr = ssh.exec_command("./users.create_xdm.sh")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
print('Successfully Created Users in Homer')

sftp.close()
ssh.close()
