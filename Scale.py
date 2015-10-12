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

############################## logging ########################################
import logging
import datetime
now = datetime.datetime.now()
date_time = now.strftime("%Y-%m-%d_%H-%M")
filename_activity = '/root/vIMS/logs/Scale_up_' + date_time + '.log'
filename_error = '/root/vIMS/logs/Scale_up_error_' + date_time + '.log'

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

def scale_up():
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
 logger.info("Getting credentials")
 def get_configurations():
 	file = open(CONFIG_PATH)
 	configurations = json.load(file)
 	file.close()
 	return configurations
 print('Credentials Loaded')  
 config = get_configurations()
 
 logger.info("Getting Keystone credentials")
 credsks = get_keystone_creds(config)
 logger_nova.info("Getting nova credentials")
 creds = get_nova_creds(config)
 
 # Get authorized instance of nova client
 logger_nova.info("Getting authorized instance of nova client")
 nova = nvclient.Client(**creds)   
 logger_neutron.info("Get authorized instance of neutron client")
 # Get authorized instance of neutron client
 neutron = ntrnclient.Client(**credsks)
 
 ########################### Create Heat Stack from credentials of keystone #####################
 logger_neutron.info("Create Heat Stack from credentials of keystone")
 cred = get_keystone_creds(config)
 logger.info("Creating Keystone credentials")
 ks_client = Keystone_Client(**cred)
 heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
 logger.info("Creating heat client")
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
 
 ##################################### Get DNS IP ################################################
 
 def get_dns_ip(heat, cluster_name):
    cluster_full_name=cluster_name
    cluster_details=heat.stacks.get(cluster_full_name)
    
    for i in cluster_details.outputs:
      if i['output_key']=='dns_ip':
         dns_ip= i['output_value']
    return dns_ip
 
 dns_ip = get_dns_ip(heatclient , STACK_NAME)   
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
 logger.info("Fetch network ID of network netname/external network")
 print ('Network ID of external network =' + net_id)
 #Create variable for indexing clearwater nodes
 index = 1
 index = str(index)
 
 ################################# Configure Homestead Node ######################################
 #Get Homestead IP
 logger.info("Getting Homestead IP")
 homestead_ip = get_homestead_ip(heatclient , STACK_NAME)
 
 #Connect to Homestead
 #k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
 logger_ssh.info("Creating SSh client")
 ssh = paramiko.SSHClient()
 ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
 logger_ssh.info("Connecting To Homestead Node")
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
     
     
 stdin, stdout, stderr = ssh.exec_command("snmpwalk -v2c -c clearwater localhost PROJECT-CLEARWATER-MIB::homesteadIncomingRequestsCount.scopeCurrent5MinutePeriod ")
 mib_data = stdout.read()
 mib_data = str(mib_data)
 data = mib_data.split()
 no_of_incomming_requests =  data[3]
 print no_of_incomming_requests 
 
 
 logger.info("Getting network ID of private network")
 private_net_id = get_network_id('IMS-private', neutron)
 print ('Network ID of private network =' + private_net_id)
 if (int(no_of_incomming_requests) > int(CALL_THRESHOLD)):
 ############################### Heat Stack Create ##########################################
   def create_cluster(heat,cluster_name):
     cluster_full_name=cluster_name
 
     file_main= open('/root/AB/scale.yaml', 'r')                
     file_bono= open('/root/AB/bono.yaml', 'r')
     file_sprout= open('/root/AB/sprout.yaml', 'r')
     file_ralf= open('/root/AB/ralf.yaml', 'r')
     file_homestead= open('/root/AB/homestead.yaml', 'r')
 
     cluster_body={
      "stack_name":cluster_full_name,
      "template":file_main.read(),
      "files":{
         "bono.yaml":file_bono.read(),
         "homestead.yaml": file_homestead.read(),
         "sprout.yaml": file_sprout.read(),
         "ralf.yaml": file_ralf.read(),
        },
        "parameters": {
        "public_net_id": net_id,
        "private_net_id": private_net_id,
        "zone" : domain,
        "flavor": "m1.medium",
        "image": "IMS",     
   	   "dnssec_key": "evGkzu+RcZA1FMu/JnbTO55yMNbnrCNVHGyQ24z/hTpSRIo6Bm9+QYmr48Lps6DsYKGepmUUwEpeBoZIiv8c1Q==",
   	   "key_name":"secure",
        "index":index,  
        "dns_ip":dns_ip,
 #       "availability_zone":"compute1"
        }
       }
     #try:  
     heat.stacks.create(**cluster_body)
     #except:
     #print ("There is an Err creating cluster, exiting...")
     #sys.exit()
     print ("Creating stack "+ cluster_full_name )
     
 ########################### Create Heat Stack from credentials of keystone #####################
 
   logger.info("Create Heat Stack from credentials of keystone")
   logger.info("Getting Keystone credentials")
   cred = get_keystone_creds(config)
   logger.info("Creating keystone Client")
   ks_client = Keystone_Client(**cred)
   heat_endpoint = ks_client.service_catalog.url_for(service_type='orchestration', endpoint_type='publicURL')
   logger.info("Creating Heat Client")
   heatclient = Heat_Client('1', heat_endpoint, token=ks_client.auth_token, username='admin', passwork='admin')
   create_cluster(heatclient,SCALE_STACK_NAME)
   #stack = heatclient.stacks.list()
   #print stack.next()
   print('Please wait while stack is deployed.......')
   #time.sleep(180)
   cluster_details=heatclient.stacks.get(SCALE_STACK_NAME)
   while(cluster_details.status!= 'COMPLETE'):
      time.sleep(30)
      if cluster_details.status == 'IN_PROGRESS':
        logger.info("Stack Creation in progress")
		print('Stack Creation in progress..')
      cluster_details=heatclient.stacks.get(SCALE_STACK_NAME)    
      
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
   logger.info("Configuring Bono Node")
   #Delay to allow for the node to spawn
   time.sleep(180)
   #Get Bono IP
   logger.info("Getting Bono IP")
   bono_ip = get_bono_ip(heatclient , SCALE_STACK_NAME)
   
   #Connect to Bono
   while True:
     try:
   #    k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
       ssh = paramiko.SSHClient()
       ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	   logger_ssh.info("Connecting To Bono Node")
       print ("Connecting To Bono Node with IP " + bono_ip)
       ssh.connect( hostname = bono_ip , username = "root", password = "root123" )
       logger.info("Connected To Bono Node")
	   print ("Connected")
       break
     except:
       error_logger.exception("Could not connect Bono Node")
	   print("Could not connect. Retrying in 5 seconds...")
       time.sleep(5) 
   
   
   # Log all output to file.
   stdin, stdout, stderr = ssh.exec_command("exec > >(tee -a /var/log/clearwater-heat-bono.log) 2>&1")
   
   # Configure the APT software source.
   print("Configuring APT software source")
   logger.info("Configuring APT software source")
   stdin, stdout, stderr = ssh.exec_command("echo 'deb "+REPO_URL+" binary/' > /etc/apt/sources.list.d/clearwater.list")
   stdin, stdout, stderr = ssh.exec_command("curl -L http://repo.cw-ngv.com/repo_key | apt-key add -")
   stdin, stdout, stderr = ssh.exec_command("apt-get update")
   
   # Configure /etc/clearwater/local_config.
   print ("Configuring clearwater local settings")
   logger.info("Configuring clearwater local settings")
   stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/clearwater")
   stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
   stdout.flush()
   stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
   bono_host = stdout.read()
   bono_host = str(bono_host)
   print('BONO Private IP = '+bono_host)
   stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
   stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
   stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
   stdin.write('local_ip='+bono_host+'\n')
   stdin.flush()
   stdin.write('public_ip='+bono_ip+'\n')
   stdin.flush()
   stdin.write('public_hostname=bono-'+index+'.'+domain+'\n')
   stdin.flush()
   stdin.write('etcd_cluster="192.168.0.1,192.168.0.3,192.168.0.4,192.168.0.5,192.168.0.6,192.168.0.7,192.168.0.8"')
   stdin.channel.shutdown_write()
   
   # Configure and upload /etc/clearwater/shared_config.
   print ("Configuring clearwater shared settings")
   logger.info("Configuring clearwater shared settings")
   stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/shared_config")
   stdin.write('home_domain='+domain+'\n')
   stdin.flush()
   stdin.write('sprout_hostname=sprout.'+domain+'\n')
   stdin.flush()
   stdin.write('hs_hostname=hs.'+domain+':8888\n')
   stdin.flush()
   stdin.write('hs_provisioning_hostname=hs.'+domain+':8889\n')
   stdin.flush()
   stdin.write('ralf_hostname=ralf.'+domain+':10888\n')
   stdin.flush()
   stdin.write('xdms_hostname=homer.'+domain+':7888\n')
   stdin.write('\n')
   stdin.flush()
   stdin.write('# Email server configuration\n')
   stdin.flush()
   stdin.write('smtp_smarthost=localhost\n')
   stdin.flush()
   stdin.write('smtp_username=username\n')
   stdin.flush()
   stdin.write('smtp_password=password\n')
   stdin.flush()
   stdin.write('email_recovery_sender=clearwater@dellnfv.org\n')
   stdin.flush()
   stdin.write('\n')
   stdin.flush()            
   stdin.write('# Keys\n')
   stdin.flush()
   stdin.write('signup_key=secret\n')
   stdin.flush()
   stdin.write('turn_workaround=secret\n')
   stdin.flush()
   stdin.write('ellis_api_key=secret\n')
   stdin.flush()
   stdin.write('ellis_cookie_key=secret\n')
   stdin.channel.shutdown_write()
   
   print('Updating Ubuntu')
   logger.info("Updating Ubuntu")
   stdin, stdout, stderr = ssh.exec_command("sudo apt-get update")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("sudo apt-get update")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
        
   # Installing the software
   print('Installing Bono packages....')
   logger.info("Installing Bono packages.")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install bono --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install bono --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break
   	
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break
   
   # Installing the software
   print('Installing Bono packages....')
   logger.info("Installing Bono packages.")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install bono --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install bono --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break	
   
   print('Installing SNMP...')
   logger.info("Installing SNMP.")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
   
   print('Installing SNMPD...')
   logger.info("Installing SNMPD.")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
   print('Finished Installation..')
   logger.info("Finished Installation in BONO")
   		
   print('Uploading shared configuration')
   logger.info("Uploading shared configuration")
   stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/upload_shared_config")
   #Display Output on screen
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   print('Applying shared configuration')
   logger.info("Applying shared configuration")
   stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/apply_shared_config")	
   #Display Output on screen
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   
   #Update DNS Server
   print('Updating DNS server')
   logger.info("Updating DNS server")
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
   stdin.write('update add bono-'+index+'.'+domain+'. 30 A '+bono_ip+'\n')
   stdin.flush()
   stdin.write('update add '+domain+'. 30 A '+dns_ip+'\n')
   stdin.flush()
   stdin.write('update add '+domain+'. 30 NAPTR 0 0 "s" "SIP+D2T" "" _sip._tcp.'+domain+'.\n')
   stdin.flush()
   stdin.write('update add '+domain+'. 30 NAPTR 0 0 "s" "SIP+D2U" "" _sip._udp.'+domain+'.\n')
   stdin.flush()
   stdin.write('update add _sip._tcp.'+domain+'. 30 SRV 0 0 5060 bono-'+index+'.'+domain+'.\n')
   stdin.flush()
   stdin.write('update add _sip._udp.'+domain+'. 30 SRV 0 0 5060 bono-'+index+'.'+domain+'.\n')
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
   
   print('Checking cluster state')
   logger.info("Checking cluster state")
   stdin, stdout, stderr = ssh.exec_command("/usr/share/clearwater/clearwater-cluster-manager/scripts/check_cluster_state")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   print('Checking cluster configurations')  
   logger.info("Checking cluster configurations")
   stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/check_config_sync")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),      
         
   ssh.close()
      
 ################################### Configure Homestead Node ######################################
   #Get Homestead IP
   logger.info("Configure Homestead Node")
   logger.info("Get Homestead IP")
   homestead_ip = get_homestead_ip(heatclient , SCALE_STACK_NAME)
   
   #Connect to Homestead
   #k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
   ssh = paramiko.SSHClient()
   ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   logger_ssh.info("Connecting To Homestead Node")
   print ("Connecting To Homestead Node with IP " + homestead_ip)
   ssh.connect( hostname = homestead_ip , username = "root", password = "root123" )
   logger.info("Connected To Homestead Node")
   print ("Connected")
   stdin, stdout, stderr = ssh.exec_command("sudo -s")  
   
   # Log all output to file.
   stdin, stdout, stderr = ssh.exec_command("exec > >(tee -a /var/log/clearwater-heat-homestead.log) 2>&1")
   stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
   homestead_host = stdout.read()
   homestead_host = str(homestead_host)
   
   # Configure the APT software source.
   print("Configuring APT software source")
   logger.info("Configuring APT software source")
   stdin, stdout, stderr = ssh.exec_command("echo 'deb "+REPO_URL+" binary/' > /etc/apt/sources.list.d/clearwater.list")
   stdin, stdout, stderr = ssh.exec_command("curl -L http://repo.cw-ngv.com/repo_key | apt-key add -")
   stdin, stdout, stderr = ssh.exec_command("apt-get update")
   
   # Configure /etc/clearwater/local_config.
   print ("Configuring clearwater local settings")
   logger.info("Configuring clearwater local settings")
   stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/clearwater")
   stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
   stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
   stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
   stdin.write('local_ip='+homestead_host+'\n')
   stdin.flush()
   stdin.write('public_ip='+homestead_ip+'\n')
   stdin.flush()
   stdin.write('public_hostname=homestead-'+index+'.'+domain+'\n')
   stdin.flush()
   stdin.write('etcd_cluster="192.168.0.1,192.168.0.3,192.168.0.4,192.168.0.5,192.168.0.6,192.168.0.7,192.168.0.8"')
   stdin.channel.shutdown_write()
   
   # Configure and upload /etc/clearwater/shared_config.
   print ("Configuring clearwater shared settings")
   logger.info("Configuring clearwater shared settings")
   stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/shared_config")
   stdin.write('home_domain='+domain+'\n')
   stdin.flush()
   stdin.write('sprout_hostname=sprout.'+domain+'\n')
   stdin.flush()
   stdin.write('hs_hostname=hs.'+domain+':8888\n')
   stdin.flush()
   stdin.write('hs_provisioning_hostname=hs.'+domain+':8889\n')
   stdin.flush()
   stdin.write('ralf_hostname=ralf.'+domain+':10888\n')
   stdin.flush()
   stdin.write('xdms_hostname=homer.'+domain+':7888\n')
   stdin.write('\n')
   stdin.flush()
   stdin.write('# Email server configuration\n')
   stdin.flush()
   stdin.write('smtp_smarthost=localhost\n')
   stdin.flush()
   stdin.write('smtp_username=username\n')
   stdin.flush()
   stdin.write('smtp_password=password\n')
   stdin.flush()
   stdin.write('email_recovery_sender=clearwater@dellnfv.org\n')
   stdin.flush()
   stdin.write('\n')
   stdin.flush()            
   stdin.write('# Keys\n')
   stdin.flush()
   stdin.write('signup_key=secret\n')
   stdin.flush()
   stdin.write('turn_workaround=secret\n')
   stdin.flush()
   stdin.write('ellis_api_key=secret\n')
   stdin.flush()
   stdin.write('ellis_cookie_key=secret\n')
   stdin.channel.shutdown_write()
   
   print('Updating Ubuntu')
   stdin, stdout, stderr = ssh.exec_command("sudo apt-get update")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("sudo apt-get update")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break            
   # Now install the software.
   print('Installing Homestead packages...')
   logger.info("Installing Homestead packages.")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
       logger.info("Retrying Installation.")
	   print('Retrying Installation...')
       time.sleep(5)	
     else:
       break
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f homestead homestead-prov --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f homestead homestead-prov --yes --force-yes -o DPkg::options::=--force-confnew")
       logger.info("Retrying Installation.")
	   print('Retrying Installation...')
       time.sleep(5)	
     else:
       break			
   print('Installing clearwater management packages')
   logger.info("Installing clearwater management packages")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f clearwater-management --yes --force-yes")   
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f clearwater-management --yes --force-yes")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break		
   
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if('Err' in stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f clearwater-cassandra --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f homestead homestead-prov --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if('Err' in stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f homestead homestead-prov --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break
   
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f clearwater-snmp-handler-homestead --yes --force-yes")   
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f clearwater-snmp-handler-homestead --yes --force-yes")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break		    		
   
   print('Installing SNMP...')
   logger.info("Installing SNMP in Homestead")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
   
   print('Installing SNMPD...')
   logger.info("Installing SNMPD in Homestead")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install -f snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
   print('Finished Installation..')
   logger.info("Finished Installation in Homestead")
   		    
   print('Installed Homestead packages')	
   
   #Configure MIB's
   print('Configuring SNMP')
   logger.info("Configure MIB's in Homer")
   sftp = ssh.open_sftp()
   sftp.put( MIB_FILE_PATH, MIB_PATH )
   sftp.put( MIB_FILE_PATH, '/usr/share/snmp/mibs/PROJECT-CLEARWATER-MIB.txt')
   sftp.put( SNMP_FILE_PATH, SNMP_CONFIG_PATH )
   stdin, stdout, stderr = ssh.exec_command("service snmpd restart")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   time.sleep(30)
   stdin, stdout, stderr = ssh.exec_command("snmpwalk -v 2c -c clearwater localhost UCD-SNMP-MIB::memory")
   
   	
   print('Uploading shared configuration')
   logger.info("Uploading shared configuration")
   stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/upload_shared_config")
   #Display Output on screen
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   print('Applying shared configuration')
   logger.info("Applying shared configuration")
   stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/apply_shared_config")	
   #Display Output on screen
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   
   #Update DNS Server
   print('Updating DNS server')
   logger.info("Updating DNS server for homestead")
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
   stdin.write('update add homestead-'+index+'.'+domain+'. 30 A '+homestead_ip+'\n')
   stdin.flush()
   stdin.write('update add hs.'+domain+'. 30 A '+homestead_host+'\n')
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
    
   #Check cluster settings
   stdin, stdout, stderr = ssh.exec_command("/usr/share/clearwater/clearwater-cluster-manager/scripts/check_cluster_state")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   
   stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/check_config_sync")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024), 
   ssh.close()
   
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
   logger.info("Configure Ralf Node")
   logger.info("Get Ralf IP")
   while True:
     try:
       ralf_ip = get_ralf_ip(heatclient , SCALE_STACK_NAME)
       break
     except:
       print('Getting Ralf IP failed. Retring in 5 seconds...')
	   error_logger.exception("Getting Ralf IP failed. Retrying")
       time.sleep(5)
   
   #Connect to Ralf
   while True:
     try:
   #    k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
       ssh = paramiko.SSHClient()
       ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
       logger_ssh.info("Connecting To Ralf Node")
	   print ("Connecting To Ralf Node with IP " + ralf_ip)
	   
       ssh.connect( hostname = ralf_ip , username = "root", password = "root123" )
       logger_ssh.info("Connected To Ralf Node")
	   print ("Connected")
       break
     except:
       print("Could not connect. Retrying in 5 seconds...")
	   error_logger.exception("Could not connect to Ralf.")
       time.sleep(5) 
   
   # Log all output to file.
   stdin, stdout, stderr = ssh.exec_command("exec > >(tee -a /var/log/clearwater-heat-ellis.log) 2>&1")
   
   # Configure the APT software source.
   print("Configuring APT software source")
   logger.info("Configuring APT software source")
   stdin, stdout, stderr = ssh.exec_command("echo 'deb "+REPO_URL+" binary/' > /etc/apt/sources.list.d/clearwater.list")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   stdin, stdout, stderr = ssh.exec_command("curl -L http://repo.cw-ngv.com/repo_key | apt-key add -")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   stdin, stdout, stderr = ssh.exec_command("apt-get update")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   
   
   #Get Private IP address
   stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
   ralf_host = stdout.read()
   ralf_host = str(ralf_host)
   
   # Configure /etc/clearwater/local_config.
   print ("Configuring clearwater local settings")
   logger.info("Configuring clearwater local settings")
   stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/clearwater")
   stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
   stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
   stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
   stdin.write('local_ip='+ralf_host+'\n')
   stdin.flush()
   stdin.write('public_ip='+ralf_ip+'\n')
   stdin.flush()
   stdin.write('public_hostname=ralf-'+index+'.'+domain+'\n')
   stdin.flush()
   stdin.write('etcd_cluster="192.168.0.1,192.168.0.3,192.168.0.4,192.168.0.5,192.168.0.6,192.168.0.7,192.168.0.8"')
   stdin.channel.shutdown_write()
   
   print('Updating Ubuntu')
   stdin, stdout, stderr = ssh.exec_command("sudo apt-get update")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
        
   # Installing the software
   print ("Installing Ralf software packages....")
   logger.info("Installing Ralf software packages.")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install ralf --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print 'Installing....'
   			time.sleep(30)
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install ralf --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break				
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes") 
   print ("Installed Ralf packages")
   logger.info("Installed Ralf software packages.")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print 'Installing....'
   			time.sleep(30)
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break		
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-chronos --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print 'Installing....',
   			time.sleep(30)
   
   while True:	
     if('Err' in stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-chronos --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break     
   
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-astaire --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print 'Installing....',
   			time.sleep(30)
   
   while True:	
     if('Err' in stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-astaire --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break     
   print('Installing SNMP...')
   logger.info("Installing SNMP in Ralf")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
   
   print('Installing SNMPD...')
   logger.info("Installing SNMPD in Ralf")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
   print('Finished Installation..')
   logger.info("Finished Installation in Ralf")
   		 
   print('Installed Ralf packages') 
   #Update DNS Server
   print('Updating DNS server')
   logger.info("Updating DNS server for Ralf")
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
   stdin.write('update add ralf-'+index+'.'+domain+'. 30 A '+ralf_ip+'\n')
   stdin.flush()
   stdin.write('update add ralf.'+domain+'. 30 A '+ralf_host+'\n')
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
   
   #Check cluster settings
   stdin, stdout, stderr = ssh.exec_command("/usr/share/clearwater/clearwater-cluster-manager/scripts/check_cluster_state")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   
   stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/check_config_sync")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024), 
   ssh.close()
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
   logger.info("configuring sprout")
   logger.info("Get Sprout IP")
   sprout_ip = get_sprout_ip(heatclient , SCALE_STACK_NAME)
   
   #Connect to Sprout
   #k = paramiko.RSAKey.from_private_key_file("/root/.ssh/secure.pem")
   ssh = paramiko.SSHClient()
   ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   logger_ssh.info("Connecting To Sprout Node")
   print ("Connecting To Sprout Node with IP " + sprout_ip)
   ssh.connect( hostname = sprout_ip , username = "root", password = "root123" )
   logger.info("Connected to Sprout")
   print ("Connected")
   stdin, stdout, stderr = ssh.exec_command("sudo -s")  
   
   # Log all output to file.
   stdin, stdout, stderr = ssh.exec_command("exec > >(tee -a /var/log/clearwater-heat-ellis.log) 2>&1")
   stdin, stdout, stderr = ssh.exec_command("(hostname -I)")
   sprout_host = stdout.read()
   sprout_host = str(sprout_host)
   
   # Configure the APT software source.
   print("Configuring APT software source")
   logger.info("Configuring APT software source")
   stdin, stdout, stderr = ssh.exec_command("echo 'deb "+REPO_URL+" binary/' > /etc/apt/sources.list.d/clearwater.list")
   stdin, stdout, stderr = ssh.exec_command("curl -L http://repo.cw-ngv.com/repo_key | apt-key add -")
   stdin, stdout, stderr = ssh.exec_command("apt-get update")
   
   # Configure /etc/clearwater/local_config.
   print ("Configuring clearwater local settings")
   logger.info("Configuring clearwater local settings")
   stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/clearwater")
   stdin, stdout, stderr = ssh.exec_command("etcd_ip="+ETCD_IP)
   stdin, stdout, stderr = ssh.exec_command('[ -n "$etcd_ip" ] || etcd_ip=$(hostname -I)')
   stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/local_config")
   stdin.write('local_ip='+sprout_host+'\n')
   stdin.flush()
   stdin.write('public_ip='+sprout_ip+'\n')
   stdin.flush()
   stdin.write('public_hostname=sprout-'+index+'.'+domain+'\n')
   stdin.flush()
   stdin.write('etcd_cluster="192.168.0.1,192.168.0.3,192.168.0.4,192.168.0.5,192.168.0.6,192.168.0.7,192.168.0.8"')
   stdin.channel.shutdown_write()
   
   # Configure and upload /etc/clearwater/shared_config.
   print ("Configuring clearwater shared settings")
   logger.info("Configuring clearwater shared settings")
   stdin, stdout, stderr = ssh.exec_command("cat > /etc/clearwater/shared_config")
   stdin.write('home_domain='+domain+'\n')
   stdin.flush()
   stdin.write('sprout_hostname=sprout.'+domain+'\n')
   stdin.flush()
   stdin.write('hs_hostname=hs.'+domain+':8888\n')
   stdin.flush()
   stdin.write('hs_provisioning_hostname=hs.'+domain+':8889\n')
   stdin.flush()
   stdin.write('ralf_hostname=ralf.'+domain+':10888\n')
   stdin.flush()
   stdin.write('xdms_hostname=homer.'+domain+':7888\n')
   stdin.write('\n')
   stdin.flush()
   stdin.write('# Email server configuration\n')
   stdin.flush()
   stdin.write('smtp_smarthost=localhost\n')
   stdin.flush()
   stdin.write('smtp_username=username\n')
   stdin.flush()
   stdin.write('smtp_password=password\n')
   stdin.flush()
   stdin.write('email_recovery_sender=clearwater@dellnfv.org\n')
   stdin.flush()
   stdin.write('\n')
   stdin.flush()            
   stdin.write('# Keys\n')
   stdin.flush()
   stdin.write('signup_key=secret\n')
   stdin.flush()
   stdin.write('turn_workaround=secret\n')
   stdin.flush()
   stdin.write('ellis_api_key=secret\n')
   stdin.flush()
   stdin.write('ellis_cookie_key=secret\n')
   stdin.channel.shutdown_write()
   
   # Create /etc/chronos/chronos.conf.
   logger.info("Create /etc/chronos/chronos.conf.")
   stdin, stdout, stderr = ssh.exec_command("mkdir -p /etc/chronos")
   stdin, stdout, stderr = ssh.exec_command("cat > /etc/chronos/chronos.conf")
   stdin.write('[http]\n')
   stdin.flush()
   stdin.write('bind-address = '+sprout_host+'\n')
   stdin.flush()
   stdin.write('bind-port = 7253\n')
   stdin.flush()
   stdin.write('threads = 50\n')
   stdin.flush()
   stdin.write('\n')
   stdin.flush()
   stdin.write('[logging]\n')
   stdin.flush()
   stdin.write('folder = /var/log/chronos\n')
   stdin.flush()
   stdin.write('level = 2\n')
   stdin.flush()
   stdin.write('\n')
   stdin.flush()
   stdin.write('[alarms]\n')
   stdin.flush()
   stdin.write('enabled = true\n')
   stdin.flush()
   stdin.write('\n')
   stdin.flush()
   stdin.write('[exceptions]\n')
   stdin.flush()
   stdin.write('max_ttl = 600\n')
   stdin.flush()
   stdin.channel.shutdown_write()
   
   print('Updating Ubuntu')
   logger.info("Updating Ubuntu")
   stdin, stdout, stderr = ssh.exec_command("sudo apt-get update")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("sudo apt-get update")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("sudo apt-get update")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break                
   # Now install the software.
   print('Installing Sprout packages....')
   logger.info("Installing Sprout packages.")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install sprout --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print 'Installing....',
   			time.sleep(30)
   
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install sprout --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break
   	
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-management --yes --force-yes")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print 'Installing....'
   			time.sleep(30)
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-config-manager --yes --force-yes")
       print('Retrying Installation...')
	   logger.info("Retrying Installation.")
       time.sleep(5)	
     else:
       break			
   
   print('Installing Sprout packages....')
   logger.info("Installing Sprout packages.")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install sprout --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print 'Installing....',
   			time.sleep(30)
   
   while True:	
     if('Err' in stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install sprout --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
       
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-chronos --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print 'Installing....',
   			time.sleep(30)
   
   while True:	
     if('Err' in stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-chronos --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break     
   
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-astaire --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print 'Installing....',
   			time.sleep(30)
   
   while True:	
     if('Err' in stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install clearwater-snmp-handler-astaire --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break     
   print('Installing SNMP...')
   logger.info("Installing SNMP in Sprout")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmp snmp-mibs-downloader --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
   
   print('Installing SNMPD...')
   logger.info("Installing SNMPD in Sprout")
   stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   while True:	
     if(not stdout.read()):
       stdin, stdout, stderr = ssh.exec_command("DEBIAN_FRONTEND=noninteractive apt-get install snmpd --yes --force-yes -o DPkg::options::=--force-confnew")
       print('Retrying Installation...')
       time.sleep(5)	
     else:
       break    
   print('Finished Installation..')
   logger.info("Finished Installation")
   		 
          
   print('Installed Sprout packages')
   	
   print('Uploading shared configuration')
   logger.info("Uploading shared configuration")
   stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/upload_shared_config")
   #Display Output on screen
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   print('Applying shared configuration')
   stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/apply_shared_config")	
   #Display Output on screen
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   
   #Update DNS Server
   print('Updating DNS server')
   logger_ssh.info("Updating DNS server")
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
   stdin.write('update add sprout-'+index+'.'+domain+'. 30 A '+sprout_host+'\n')
   stdin.flush()
   stdin.write('update add sprout.'+domain+'. 30 A '+sprout_host+'\n')
   stdin.flush()
   stdin.write('update add sprout.'+domain+'. 30 NAPTR 0 0 "s" "SIP+D2T" "" _sip._tcp.sprout.'+domain+'.\n')
   stdin.flush()
   stdin.write('update add _sip._tcp.sprout.'+domain+'. 30 SRV 0 0 5054 sprout-'+index+'.'+domain+'.\n')
   stdin.flush()
   stdin.write('update add icscf.sprout.'+domain+'. 30 NAPTR 0 0 "s" "SIP+D2T" "" _sip._tcp.icscf.sprout.'+domain+'.\n')
   stdin.flush()
   stdin.write('update add _sip._tcp.icscf.sprout.'+domain+'. 30 SRV 0 0 5052 sprout-'+index+'.'+domain+'.\n')
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
   
   #Check cluster settings
   stdin, stdout, stderr = ssh.exec_command("/usr/share/clearwater/clearwater-cluster-manager/scripts/check_cluster_state")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024),
   
   stdin, stdout, stderr = ssh.exec_command("sudo /usr/share/clearwater/clearwater-config-manager/scripts/check_config_sync")
   while not stdout.channel.exit_status_ready():
   	# Only print data if there is data to read in the channel 
   	if stdout.channel.recv_ready():
   		rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
   		if len(rl) > 0:
   			# Print data from stdout
   			print stdout.channel.recv(1024), 
   ssh.close()  