import os
import sys
import time
import readline
import json

def keypair_exists(nova ,key_name):
	
	keypair_exists = False
	
	list1 = nova.keypairs.list()
	for x in list1:
		if x.name == key_name:
			keypair_exists= True 
	
	return keypair_exists



def image_exists(glance, img_name):
	
	img_exists = False
	
	images = glance.images.list()
	while True:
		try:
			image = images.next()
			if (img_name == image.name):
				img_exists = True
				return img_exists
			#print image.name + ' - ' + image.id
		except StopIteration:
			break
	return img_exists	



def get_stack_private_ip(heat, cluster_name, PATH):
     temp_list=[]
     cluster_full_name=cluster_name
     cluster_details=heat.stacks.get(cluster_full_name)
     file = open(PATH+ "/Private_net_ip.txt", "a")
     for i in cluster_details.outputs:
       if i['output_key']=='homestead_ip_private':
          homestead_ip_private= i['output_value']
          file.write(homestead_ip_private[0] + ",")
       if i['output_key']=='dns_ip_private':
          dns_ip_private= i['output_value']
          file.write(dns_ip_private + ",")
       if i['output_key']=='homer_ip_private':
          homer_ip_private= i['output_value']
          file.write(homer_ip_private[0] + ",")
       if i['output_key']=='bono_ip_private':
          bono_ip_private= i['output_value']
          file.write(bono_ip_private[0] + ",")
       if i['output_key']=='sprout_ip_private':
          sprout_ip_private= i['output_value']
          file.write(sprout_ip_private[0] + ",")
       if i['output_key']=='ellis_ip_private':
          ellis_ip_private= i['output_value']
          file.write(ellis_ip_private +"," )
       if i['output_key']=='ralf_ip_private':
          ralf_ip_private= i['output_value']
          file.write(ralf_ip_private[0] + ",")
     file.close()
	
     file1 = open(PATH+ "/Private_net_ip.txt", "r")
     Stack_private_ip= file1.read()
     file1.close()
     return Stack_private_ip
	 
   

	
