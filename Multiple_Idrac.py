import string
import paramiko
import re
import subprocess,math
from math import *
from subprocess import *
import os
import json
import pandas as pd
from datetime import datetime
from ConfigParser import *
from ConfigParser import (ConfigParser, MissingSectionHeaderError,
                          ParsingError, DEFAULTSECT)
import ConfigParser
import collections


NoOfIdracs = input('Enter the number of IDRACs :')

IdracList=[]
for i in range(0,NoOfIdracs):
	Idrac=[]
	IpAddress=raw_input('Enter the IP Address for IDRAC :')
        Idrac.append (IpAddress)
        User=raw_input('Enter the user name for IDRAC :')
        Idrac.append (User)
        Pass=raw_input('Enter the Password for IDRAC  :')
        Idrac.append (Pass)
        IdracList.append(Idrac)


#print IdracList

HwInventoryList=[]
for idracNo in range(0,len(IdracList)):
	ssh=paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		ssh.connect(IdracList[idracNo][0],username=IdracList[idracNo][1],password=IdracList[idracNo][2])
		stdin,stdout,stderr=ssh.exec_command("racadm hwinventory")
	        HwInventoryList.append(stdout.readlines())
        	ssh.close()
	except Exception as e:
		print ("ssh.connect not work for %s",IdracList[idracNo][0])
	

print "HWInventory"
print HwInventoryList
print "Length of HwInventory: %s"%len(HwInventoryList)

search_dimm = "InstanceID: DIMM.Socket"
search_size = "Size ="

search_cpu = "InstanceID: CPU.Socket"
search_nfp = "NumberOfProcessorCores"
search_ht = "HyperThreadingEnabled = Yes"
search_nic = "InstanceID: NIC.Integrated"

dumy_mem=''
dumy_cpu=''
dumy_nic=''

dmem=''
dcpu=''
dcpu=''

dumy_mem_list=[]
dumy_cpu_list=[]
TotalIdracsOutputs=len(HwInventoryList)




Result=[]


System_dictionary={}
Sys_mem_dic={}
Sys_cpu_dic={}
leave=1
for IdracNo in range(0,TotalIdracsOutputs):
	
	MemoryDictionary={}
	
	Mem_section_list,mem_size_list,mem_speed_list,mem_descp_list,mem_serial_list,mem_model_list,mem_status_list=([]for i in range(0,7))

	dumy_mem_dic=collections.defaultdict(dict)
	
	time=datetime.utcnow().strftime("%s")
	filename ="Idrac"+str(IdracNo)+"_"+time+".ini"
	fptr= open(filename,"w+")
	
	for line in HwInventoryList[IdracNo]:
		if "--" in line:
			continue
		fptr.write("%s\n" % line) 
#	fptr.write(HwInventoryList[IdracNo])
	fptr.close()	
	
	Config = ConfigParser.ConfigParser()
	Config.read(filename)
#	print "Config Section ",Config.sections()
	#dumy_result=json.dumps(HwInventoryList[IdracNo])
	#Result.append(dumy_result)	
	
	Mem_section_list = [s for s,s in enumerate(Config.sections()) if "InstanceID: DIMM.Socket" in s]
	
	for mem_sec in Mem_section_list:
		mem_size_list+=[Config.get(str(mem_sec),'Size')]
		mem_speed_list+=[Config.get(str(mem_sec),'speed')]
		mem_descp_list+=[Config.get(str(mem_sec),'Manufacturer')]
		mem_serial_list+=[Config.get(str(mem_sec),'SerialNumber')]
		mem_model_list+=[Config.get(str(mem_sec),'Model')]
		mem_status_list+=[Config.get(str(mem_sec),'PrimaryStatus')]	
	for index in range(0,len(mem_size_list)):	
		if "MB" in mem_size_list[index]:
			value=mem_size_list[index].replace("MB","")
			mem_size_list[index] = value
		elif "PB" in mem_size_list[index]:
			value=mem_size_list[index].replace("PB","")
			value*= math.pow(1024,3);	
			mem_size_list[index] = value
		elif "TB" in mem_size_list[index]:
			value=mem_size_list[index].replace("TB","")
			value*= math.pow(1024,2);	
			mem_size_list[index] = value
		elif "GB" in mem_size_list[index]:
			value=mem_size_list[index].replace("GB","")
			value*= math.pow(1024,1);	
			mem_size_list[index] = value
		elif "KB" in mem_size_list[index]:
			value=mem_size_list[index].replace("KB","")
			value/=1024	
			mem_size_list[index] = value
		

#	T_memory = sum([int(x) for x in mem_size_list])
#	print T_memory 
	
	dumy_mem_dic['extra']['slots']=len(mem_size_list)	
	dumy_mem_dic['extra']['Manufacturer']=mem_descp_list
	dumy_mem_dic['extra']['speed']=mem_speed_list
	dumy_mem_dic['extra']['model']=mem_model_list
	dumy_mem_dic['extra']['serial']=mem_serial_list
	dumy_mem_dic['extra']['speed']=mem_speed_list
	dumy_mem_dic['extra']['status']=mem_status_list
	MemoryDictionary.update(dumy_mem_dic)
	MemoryDictionary['Total Memory']= sum([int(x) for x in mem_size_list])
	
	Sys_mem_dic[IdracNo]= MemoryDictionary	
	#print Sys_mem_dic
	
	System_dictionary['Memory info'] = Sys_mem_dic
		
	Cpu_section_list,cpu_processor_list,cpu_family_list,cpu_manufac_list,cpu_curr_clock_list,cpu_model_list=([]for i in range(6))
	cpu_prim_status_list,cpu_virt_list,cpu_voltag_list,cpu_enabled_thread_list,cpu_max_clock_speed_list= ([]for i in range(5))
	cpu_ex_bus_clock_speed_list,cpu_hyper_thread_list,cpu_status_list=([]for i in range(3))

	CpuDictionary={}
	dumy_cpu_dic=collections.defaultdict(dict)
	
	Cpu_section_list = [s for s,s in enumerate(Config.sections()) if "InstanceID: CPU.Socket" in s]
	
	for cpu_sec in Cpu_section_list:
		cpu_processor_list+=[Config.get(str(cpu_sec),'NumberOfProcessorCores')]
		cpu_family_list+=[Config.get(str(cpu_sec),'CPUFamily')]
		cpu_manufac_list+=[Config.get(str(cpu_sec),'Manufacturer')]
		cpu_curr_clock_list+=[Config.get(str(cpu_sec),'CurrentClockSpeed')]
		cpu_model_list+=[Config.get(str(cpu_sec),'Model')]
		cpu_prim_status_list+=[Config.get(str(cpu_sec),'PrimaryStatus')]
		cpu_virt_list+=[Config.get(str(cpu_sec),'VirtualizationTechnologyEnabled')]
		cpu_voltag_list+=[Config.get(str(cpu_sec),'Voltage')]
		cpu_enabled_thread_list+=[Config.get(str(cpu_sec),'NumberOfEnabledThreads')]
		cpu_max_clock_speed_list+=[Config.get(str(cpu_sec),'MaxClockSpeed')]
		cpu_ex_bus_clock_speed_list+=[Config.get(str(cpu_sec),'ExternalBusCLockSpeed')]
		cpu_hyper_thread_list+=[Config.get(str(cpu_sec),'HyperThreadingEnabled')]
		cpu_status_list+=[Config.get(str(cpu_sec),'CPUStatus')]

	dumy_cpu_dic['extra']['No of Processors']=cpu_processor_list
	dumy_cpu_dic['extra']['CPU Family']=cpu_family_list
	dumy_cpu_dic['extra']['Manufacturer']=cpu_manufac_list
	dumy_cpu_dic['extra']['Current Clock Speed']=cpu_curr_clock_list
	dumy_cpu_dic['extra']['Model']=cpu_model_list
	dumy_cpu_dic['extra']['Primary Status']=cpu_prim_status_list
	dumy_cpu_dic['extra']['Virtualization Technology Enabled']=cpu_virt_list
	dumy_cpu_dic['extra']['Voltage']=cpu_voltag_list
	dumy_cpu_dic['extra']['No of Enabled Thread']=cpu_enabled_thread_list
	dumy_cpu_dic['extra']['Max Clock Speed']=cpu_max_clock_speed_list
	dumy_cpu_dic['extra']['External Bus Clock Speed']=cpu_ex_bus_clock_speed_list
	dumy_cpu_dic['extra']['Hyper Threading Enabled']=cpu_hyper_thread_list
	dumy_cpu_dic['extra']['CPU Status']=cpu_status_list
	
	CpuDictionary.update(dumy_cpu_dic)
	CpuDictionary['Total CPU']= len(Cpu_section_list)
		
	Sys_cpu_dic[IdracNo]= CpuDictionary	
#	print Sys_cpu_dic
	System_dictionary['CPU info'] = Sys_cpu_dic
	
	if leave ==1:
		continue
	OutputSize=len(HwInventoryList[IdracNo])
	for OutputIndex in range(0,len(HwInventoryList[IdracNo])):
		if search_dimm in HwInventoryList[IdracNo][OutputIndex]:
			while(OutputIndex<OutputSize):
				dmem+=HwInventoryList[IdracNo][OutputIndex+1]
				Result.append(json.dumps(dmem))
				if search_size in HwInventoryList[IdracNo][OutputIndex+1]:	
					dumy_mem+=(HwInventoryList[IdracNo][OutputIndex+1])
					break
				elif "[" in HwInventoryList[IdracNo][OutputIndex+1]:
					break
				OutputIndex+=1

		elif search_nic in HwInventoryList[IdracNo][OutputIndex]:
			while(OutputIndex<OutputSize):
				
				OutputIndex+=1

		elif search_cpu in HwInventoryList[IdracNo][OutputIndex]:
                	while(OutputIndex<OutputSize):
                       		if search_ht in HwInventoryList[IdracNo][OutputIndex+1]:
                               		hyper_thread=1

				if search_nfp in HwInventoryList[IdracNo][OutputIndex+1]:
                               		dumy_cpu+=(HwInventoryList[IdracNo][OutputIndex+1])	
					break                                
                       		elif "[" in HwInventoryList[IdracNo][OutputIndex+1]:
                            		break
                        	OutputIndex+=1
	#dumy_cpu_list.append(dumy_cpu)
	#dumy_mem_list.append(dumy_mem)
	
	memorys_array = []
	memorys_array = [int(s) for s in dumy_mem.split() if s.isdigit()]
	Memory_splitLine = dumy_mem.splitlines()
	index=0
	for line in Memory_splitLine:
        	size = line.split()[2]
        	size_type = line.split()[3]

        	if size_type == "PB":
                	memorys_array[index]=size* math.pow(1024,3)
        	elif size_type == "TB":
                	memorys_array[index]=size* math.pow(1024,2)
       		elif size_type == "GB":
			memorys_array[index]=size* math.pow(1024,1)
        	elif size_type == "KB":
                	memorys_array[index]=size/1024
        	index+=1

	total_memory = 0
	total_memory = sum([int(x) for x in memorys_array])

	print "Total Memory: %dMB / %dGB"%(total_memory,total_memory/1024)
	cpu_array = []
	cpu_array = [int(s) for s in dumy_cpu.split() if s.isdigit()]
	total_cpu = 0
	total_cpu = sum([int(x) for x in cpu_array])

	if hyper_thread==1:
		print"Hyper threading enabled; total CPU: %d"%(total_cpu*2)
	else:
		print"Hyper threading disabled; total CPU: %d"%(total_cpu)
	dumy_mem=''
	dumy_cpu=''

print System_dictionary
	

time=datetime.utcnow().strftime("%s")
#filename="Idrac"+str(IdracNo)+"_"+time+".json"
filename = filename.replace("ini","json")
fptr= open(filename,"w+")
fptr.write(json.dumps(System_dictionary))
fptr.close()

df = pd.read_json(json.dumps(System_dictionary))
df.to_excel('output.xls')
#print dumy_cpu_list
#print dumy_mem_list

#print Result
#print type(Result)
#result=''
#result=''.join(str(x) for x in Result)
#print Result
#df= pd.read_json(dumy_mem)
#df.to_excel('output.xls')	
