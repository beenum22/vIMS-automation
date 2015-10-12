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
IMAGE_PATH = '/root/IMG/trusty-server-cloudimg-amd64-disk1.img'
IMAGE_DIRECTORY = '/root/IMG/'
os.environ['IMAGE_PATH'] = '/root/vIMS/IMG'
CONFIG_PATH = '/root/AB/configurations.json'
USER_CONFIG_PATH = '/root/AB/user_config.json'
STACK_NAME = 'IMS'
REPO_URL = 'http://repo.cw-ngv.com/stable'
ETCD_IP = ''
SNMP_CONFIG_PATH = '/etc/snmp/snmpd.conf'
SNMP_FILE_PATH = '/root/AB/snmpd.conf'
MIB_PATH = "/usr/share/mibs/PROJECT-CLEARWATER-MIB.txt"
MIB_FILE_PATH = "/root/AB/PROJECT-CLEARWATER-MIB.txt"
HOMER_INDEX = '0'
DN_RANGE_START = '6505550000'
DN_RANGE_LENGTH = '1000'
CALL_THRESHOLD = '20000'
SCALE_STACK_NAME = 'Scale'
index = '1' #delete when merge in autoscaling script
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

##################################### Get DNS IP ################################################

def get_dns_ip(heat, cluster_name):
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='dns_ip':
        dns_ip= i['output_value']
   return dns_ip

dns_ip = get_dns_ip(heatclient , STACK_NAME)   
########################################## Get Bono IP ##########################################
def get_bono_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='bono_ip':
        bono_ip= i['output_value']
   return bono_ip[0]
################################### Configure Bono Node #########################################
#Get Bono IP
bono_ip = get_bono_ip(heatclient , SCALE_STACK_NAME)

#Connect to Bono
while True:
  try:
#    k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print ("Connecting To Bono Node with IP " + bono_ip)
    ssh.connect( hostname = bono_ip , username = "root", password = "root123" )
    print ("Connected")
    break
  except:
    print("Could not connect. Retrying in 5 seconds...")
    time.sleep(5) 

#Update DNS Server
print('Updating DNS server')
stdin, stdout, stderr = ssh.exec_command("cat > update.sh")
stdin.write('#!/bin/bash\n')
stdin.flush()
stdin.write('retries=0\n')
stdin.flush()
stdin.write('while ! { nsupdate -y "'+domain+':evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==" -v << EOF\n')
stdin.flush()
stdin.write('server '+dns_ip+'\n')
stdin.flush()
stdin.write('debug yes\n')
stdin.flush()
stdin.write('update delete bono-'+index+'.'+domain+'. 30 A '+bono_ip+'\n')
stdin.flush()
stdin.write('update delete '+domain+'. 30 A '+dns_ip+'\n')
stdin.flush()
stdin.write('update delete '+domain+'. 30 NAPTR 0 0 "s" "SIP+D2T" "" _sip._tcp.'+domain+'.\n')
stdin.flush()
stdin.write('update delete '+domain+'. 30 NAPTR 0 0 "s" "SIP+D2U" "" _sip._udp.'+domain+'.\n')
stdin.flush()
stdin.write('update delete _sip._tcp.'+domain+'. 30 SRV 0 0 5060 bono-'+index+'.'+domain+'.\n')
stdin.flush()
stdin.write('update delete _sip._udp.'+domain+'. 30 SRV 0 0 5060 bono-'+index+'.'+domain+'.\n')
stdin.flush()
stdin.write('send\n')			
stdin.flush()
stdin.write('EOF\n')
stdin.flush()
stdin.write('} && [ $retries -lt 10 ]\n')
stdin.flush()
stdin.write('do')
stdin.flush()
stdin.write('  retries=$((retries + 1))\n')
stdin.flush()
stdin.write("echo 'nsupdate failed - retrying (retry '$retries')...'\n")
stdin.flush()
stdin.write("sleep 5\n")
stdin.flush()
stdin.write("done\n")
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command('chmod 755 update.sh')
stdin, stdout, stderr = ssh.exec_command('./update.sh')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024), 

stdin, stdout, stderr = ssh.exec_command('sudo service bono quiesce')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor clearwater_cluster_manager')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor clearwater_config_manager')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor -g etcd')
stdin, stdout, stderr = ssh.exec_command('sudo service clearwater-etcd decommission')

###################################### Get Sprout IP ############################################
  
def get_sprout_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='sprout_ip':
        sprout_ip= i['output_value']
   return sprout_ip[0]			
  
################################### Configure Sprout Node #######################################
#Get Sprout IP
sprout_ip = get_sprout_ip(heatclient , SCALE_STACK_NAME)

#Connect to Sprout
#k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print ("Connecting To Sprout Node with IP " + sprout_ip)
ssh.connect( hostname = sprout_ip , username = "root", password = "root123" )
print ("Connected")
stdin, stdout, stderr = ssh.exec_command("sudo -s")  

stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
sprout_host = stdout.read()
sprout_host = str(sprout_host)

#Update DNS Server
print('Updating DNS server')
stdin, stdout, stderr = ssh.exec_command("cat > update.sh")
stdin.write('#!/bin/bash\n')
stdin.flush()
stdin.write('retries=0\n')
stdin.flush()
stdin.write('while ! { nsupdate -y "'+domain+':evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==" -v << EOF\n')
stdin.flush()
stdin.write('server '+dns_ip+'\n')
stdin.flush()
stdin.write('debug yes\n')
stdin.flush()
stdin.write('update delete sprout-'+index+'.'+domain+'. 30 A '+sprout_host+'\n')
stdin.flush()
stdin.write('update delete sprout.'+domain+'. 30 A '+sprout_host+'\n')
stdin.flush()
stdin.write('update delete sprout.'+domain+'. 30 NAPTR 0 0 "s" "SIP+D2T" "" _sip._tcp.sprout.'+domain+'.\n')
stdin.flush()
stdin.write('update delete _sip._tcp.sprout.'+domain+'. 30 SRV 0 0 5054 sprout-'+index+'.'+domain+'.\n')
stdin.flush()
stdin.write('update delete icscf.sprout.'+domain+'. 30 NAPTR 0 0 "s" "SIP+D2T" "" _sip._tcp.icscf.sprout.'+domain+'.\n')
stdin.flush()
stdin.write('update delete _sip._tcp.icscf.sprout.'+domain+'. 30 SRV 0 0 5052 sprout-'+index+'.'+domain+'.\n')
stdin.flush()
stdin.write('send\n')	
stdin.flush()
stdin.write('EOF\n')
stdin.flush()
stdin.write('} && [ $retries -lt 10 ]\n')
stdin.flush()
stdin.write('do')
stdin.flush()
stdin.write('  retries=$((retries + 1))\n')
stdin.flush()
stdin.write("echo 'nsupdate failed - retrying (retry '$retries')...'\n")
stdin.flush()
stdin.write("sleep 5\n")
stdin.flush()
stdin.write("done\n")
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command('chmod 755 ./update.sh')
stdin, stdout, stderr = ssh.exec_command('cd /root')
stdin, stdout, stderr = ssh.exec_command('./update.sh')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("./update.sh")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break
        
# Use the DNS server.
stdin, stdout, stderr = ssh.exec_command("echo 'nameserver "+dns_ip+"' > /etc/dnsmasq.resolv.conf")
stdin, stdout, stderr = ssh.exec_command("echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq")
stdin, stdout, stderr = ssh.exec_command("service dnsmasq force-reload")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

stdin, stdout, stderr = ssh.exec_command('sudo service sprout quiesce')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor clearwater_cluster_manager')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor clearwater_config_manager')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor -g etcd')
stdin, stdout, stderr = ssh.exec_command('sudo service clearwater-etcd decommission')

#################################### Get Homestead IP ###########################################

def get_homestead_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='homestead_ip':
        homestead_ip= i['output_value']
   return homestead_ip[0]

################################### Configure Homestead Node ####################################
#Get Homestead IP
homestead_ip = get_homestead_ip(heatclient , SCALE_STACK_NAME)

#Connect to Homestead
#k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print ("Connecting To Homestead Node with IP " + homestead_ip)
ssh.connect( hostname = homestead_ip , username = "root", password = "root123" )
print ("Connected")
stdin, stdout, stderr = ssh.exec_command("sudo -s")  
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
homestead_host = stdout.read()
homestead_host = str(homestead_host)
#Update DNS Server
print('Updating DNS server')
stdin, stdout, stderr = ssh.exec_command("cat > update.sh")
stdin.write('#!/bin/bash\n')
stdin.flush()
stdin.write('retries=0\n')
stdin.flush()
stdin.write('while ! { nsupdate -y "'+domain+':evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==" -v << EOF\n')
stdin.flush()
stdin.write('server '+dns_ip+'\n')
stdin.flush()
stdin.write('debug yes\n')
stdin.flush()
stdin.write('update delete homestead-'+index+'.'+domain+'. 30 A '+homestead_ip+'\n')
stdin.flush()
stdin.write('update delete hs.'+domain+'. 30 A '+homestead_host+'\n')
stdin.flush()
stdin.write('send\n')	
stdin.flush()
stdin.write('EOF\n')
stdin.flush()
stdin.write('} && [ $retries -lt 10 ]\n')
stdin.flush()
stdin.write('do')
stdin.flush()
stdin.write('  retries=$((retries + 1))\n')
stdin.flush()
stdin.write("echo 'nsupdate failed - retrying (retry '$retries')...'\n")
stdin.flush()
stdin.write("sleep 5\n")
stdin.flush()
stdin.write("done\n")
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command('chmod 755 update.sh')
stdin, stdout, stderr = ssh.exec_command('./update.sh')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),
while True:	
  if(not stdout.read()):
    stdin, stdout, stderr = ssh.exec_command("./update.sh")
    print('Retrying Installation...')
    time.sleep(5)	
  else:
    break		
# Use the DNS server.
stdin, stdout, stderr = ssh.exec_command("echo 'nameserver "+dns_ip+"' > /etc/dnsmasq.resolv.conf")
stdin, stdout, stderr = ssh.exec_command("echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq")
stdin, stdout, stderr = ssh.exec_command("service dnsmasq force-reload")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),		   

stdin, stdout, stderr = ssh.exec_command('sudo service homestead stop && sudo service homestead-prov stop')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor clearwater_cluster_manager')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor clearwater_config_manager')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor -g etcd')
stdin, stdout, stderr = ssh.exec_command('sudo service clearwater-etcd decommission') 

###################################### Get Ralf IP ############################################
 
def get_ralf_ip(heat, cluster_name):
   temp_list=[]
   cluster_full_name=cluster_name
   cluster_details=heat.stacks.get(cluster_full_name)
   
   for i in cluster_details.outputs:
     if i['output_key']=='ralf_ip':
        ralf_ip= i['output_value']
   return ralf_ip[0]
  
################################### Configure Ralf Node #######################################
#Get Ralf IP
while True:
  try:
    ralf_ip = get_ralf_ip(heatclient , SCALE_STACK_NAME)
    break
  except:
    print('Getting Ralf IP failed. Retring in 5 seconds...')
    time.sleep(5)

#Connect to Ralf
while True:
  try:
#    k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print ("Connecting To Ralf Node with IP " + ralf_ip)
    ssh.connect( hostname = ralf_ip , username = "root", password = "root123" )
    print ("Connected")
    break
  except:
    print("Could not connect. Retrying in 5 seconds...")
    time.sleep(5) 
stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
ralf_host = stdout.read()
ralf_host = str(ralf_host)    
print('Installed Ralf packages') 
#Update DNS Server
print('Updating DNS server')
stdin, stdout, stderr = ssh.exec_command("cat > update.sh")
stdin.write('#!/bin/bash\n')
stdin.flush()
stdin.write('retries=0\n')
stdin.flush()
stdin.write('while ! { nsupdate -y "'+domain+':evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==" -v << EOF\n')
stdin.flush()
stdin.write('server '+dns_ip+'\n')
stdin.flush()
stdin.write('debug yes\n')
stdin.flush()
stdin.write('update delete ralf-'+index+'.'+domain+'. 30 A '+ralf_ip+'\n')
stdin.flush()
stdin.write('update delete ralf.'+domain+'. 30 A '+ralf_host+'\n')
stdin.flush()
stdin.write('send\n')	
stdin.flush()
stdin.write('EOF\n')
stdin.flush()
stdin.write('} && [ $retries -lt 10 ]\n')
stdin.flush()
stdin.write('do')
stdin.flush()
stdin.write('  retries=$((retries + 1))\n')
stdin.flush()
stdin.write("echo 'nsupdate failed - retrying (retry '$retries')...'\n")
stdin.flush()
stdin.write("sleep 5\n")
stdin.flush()
stdin.write("done\n")
stdin.flush()
stdin.channel.shutdown_write()

stdin, stdout, stderr = ssh.exec_command('chmod 755 update.sh')
stdin, stdout, stderr = ssh.exec_command('cd /root')
stdin, stdout, stderr = ssh.exec_command('./update.sh')
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),

# Use the DNS server.
stdin, stdout, stderr = ssh.exec_command("echo 'nameserver "+dns_ip+"' > /etc/dnsmasq.resolv.conf")
stdin, stdout, stderr = ssh.exec_command("echo 'RESOLV_CONF=/etc/dnsmasq.resolv.conf' >> /etc/default/dnsmasq")
stdin, stdout, stderr = ssh.exec_command("service dnsmasq force-reload")
while not stdout.channel.exit_status_ready():
	# Only print data if there is data to read in the channel 
	if stdout.channel.recv_ready():
		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
		if len(rl) > 0:
			# Print data from stdout
			print stdout.channel.recv(1024),        

stdin, stdout, stderr = ssh.exec_command('sudo service ralf stop')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor clearwater_cluster_manager')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor clearwater_config_manager')
stdin, stdout, stderr = ssh.exec_command('sudo monit unmonitor -g etcd')
stdin, stdout, stderr = ssh.exec_command('sudo service clearwater-etcd decommission') 

############################ Delete Heat Stack ###########################################

def delete_cluster(heat,cluster_name):
   cluster_full_name=cluster_name
   try:
    heat.stacks.delete(cluster_full_name)
    print('Removing heat stack')
   except:
     print ("Cannot find the Cluster to be deleted. Exiting ...") 
     
delete_cluster(heatclient, SCALE_STACK_NAME)