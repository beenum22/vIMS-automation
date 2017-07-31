import paramiko
import re
import subprocess,math
from math import *
from subprocess import *
import os

ssh=paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.2.106',username='root',password='calvin')
a,b,c=ssh.exec_command("racadm hwinventory")
output = b.readlines()
ssh.close()
#print(output)


search_dimm = "InstanceID: DIMM.Socket"
search_size = "Size ="

search_cpu = "InstanceID: CPU.Socket"
search_nfp = "NumberOfProcessorCores"
search_ht = "HyperThreadingEnabled = Yes"

size_of_output=len(output)

dumy_mem=''
dumy_cpu=''

hyper_thread=0

for i in range(0,size_of_output):
	if search_dimm in output[i]:
		while(1):
			if search_size in output[i+1]:	
				dumy_mem+=(output[i+1])
				break
			elif "[" in output[i+1]:
				break
			i=i+1
	elif search_cpu in output[i]:
                while(1):
                        if search_ht in output[i+1]:
                                hyper_thread=1

			if search_nfp in output[i+1]:
                                dumy_cpu+=(output[i+1])
				break                                
                        elif "[" in output[i+1]:
                                break
                        i=i+1

	
memorys_array = [int(s) for s in dumy_mem.split() if s.isdigit()]
Memory_splitLine = dumy_mem.splitlines()
index=0
for line in Memory_splitLine:
        size = line.split()[2]
        size_type = line.split()[3]

        if size_type == "PB":
                memory_array[index]=size* math.pow(1024,3)
        elif size_type == "TB":
                memorys_array[index]=size* math.pow(1024,2)
        elif size_type == "GB":
		morys_array[index]=size* math.pow(1024,1)
        elif size_type == "KB":
                memorys_array[index]=size/1024
        index+=1


total_memory = sum([int(x) for x in memorys_array])

print "Total Memory: %dMB / %dGB"%(total_memory,total_memory/1024)

cpu_array = [int(s) for s in dumy_cpu.split() if s.isdigit()]
total_cpu = sum([int(x) for x in cpu_array])

if hyper_thread==1:
	print"Hyper threading enabled; total CPU: %d"%(total_cpu*2)
else:
	print"Hyper threading disabled; total CPU: %d"%(total_cpu)

