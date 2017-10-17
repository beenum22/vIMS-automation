version = '10.1'

try:
    import argparse
    import netaddr
    import Queue
    import time
    import getpass
    import string
    import paramiko
    import re
    from multiprocessing import Process
    import threading
    from threading import *
    # import subprocess
    import math
    from math import *
    # from subprocess import *
    import os
    import json
  #  import pandas as pd
  #  from pandas.io.json import json_normalize
    from datetime import datetime
    from ConfigParser import *
    from ConfigParser import (ConfigParser, MissingSectionHeaderError,
                              ParsingError, DEFAULTSECT)
    import ConfigParser
    import collections
    from collections import OrderedDict, Counter

    import getpass
    import sys
    import telnetlib
    from prettytable import PrettyTable

except ImportError as error:
    print "You don't have module \"{0}\" installed.".format(error.message[16:])
    exit(1)

class Inventory:
    total_memory = 0
    hpgsize = 0
    hpgnum = 0
    hostos_memcap = 0
    host_memcap_extra = 4194304  # 4GB = 4194304 KB
    dictionary = OrderedDict()
    def getHpgSize(self):
        return self.hpgsize

    def getHpgNum(self):
        return self.hpgnum

    def getHostMemcap(self):
        return self.hostos_memcap

    def getHostMemCapExtra(self):
        return self.host_memcap_extra

    def setMemory(self, memory):
        self.total_memory = memory

    def getMemory(self):
        return self.total_memory

    def calculate_size(self, size):
        sizeunit = size[-2:]
        if sizeunit == 'GB':
            return 1024 * 1024 * int(size[:-2])
        elif sizeunit == 'MB':
            return 1024 * int(size[:-2])
        
    def convertSize(self, size):
        if (size == 0):
            return '0B'
        size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size, 1024)))
        p = math.pow(1024, i)
        s = round(size / p, 2)
        return '%s %s' % (s, size_name[i])

    def showlimits(self,memory):

        host_total_memory = memory
        hpgsizes = {"1GB", "2MB"}
        memcapsize = int(self.getHostMemcap()) + int(self.getHostMemCapExtra())
        freeMem = ((int(host_total_memory) * 1024) - memcapsize)
        TempfreeMem = self.convertSize(freeMem)
        self.setMemory(TempfreeMem)
   
        hugepage_list = []
        for hpgsize in hpgsizes:
            hugepagesize = self.calculate_size(hpgsize)
            hpgnum = freeMem / hugepagesize
            hpsiz = hpgsize
            sc = {}
            sc['Size'] = hpgsize
            sc['Num'] = hpgnum
            hugepage_list.append(sc)
        
        return hugepage_list
        
    def extract_mem_size(self,fil):
        memory = 0
        Config = self.extract_section(fil)

        for s in Config.sections():
            if "InstanceID: System.Embedded" in s:
               # self.total_memory = Config.get(str(s), 'SysMemTotalSize')
                memory = Config.get(str(s), 'SysMemTotalSize').split(" ")[0] 
        return memory
    
    def ssh_idrac(self,ip,usr,pas,):
        HwList = []
        timestr = time.strftime("%Y%m%d_%H%M%S")
        filename = "Idrac" + "_" + timestr + ".ini"
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(ip, username=usr,password=pas)
            stdin, stdout, stderr = ssh.exec_command("racadm hwinventory")
            HwList = stdout.readlines()
            ssh.close()

        except Exception as e:
            print("ssh.connect not work for Idrac: %s %s %s %s\n" %
                      (ip, usr, pas, e))
            return False
        #print HwList
        fptr = open(filename, "w+")
        for line in HwList:
            if "--" in line:
                continue
            fptr.write("%s\n" % line)    
   #     self.extract_mem(filename)
        return filename


    def compareLimits(self,hp_sz_nm_list,usr_hp_dict):
#        print hp_sz_nm_list,usr_hp_dict
      #  hp_dict = {}
        for hp_avail in hp_sz_nm_list:
            if hp_avail['Size'] == usr_hp_dict['Size']:
                if hp_avail['Num'] >= usr_hp_dict['Num']:
      #              hp_dict[hp_avail['Size']] = "Available"
                    check = 1
                else:
     #               hp_dict[hp_avail['Size']] = "Not Available"
                    check = 0
        return check            
    #    return hp_dict,check
    
    def verify_memory(self, nodes, ipmi_user, ipmi_pass,hp_dic):
      #  hp_list = []
       # print hp_dic
        val_list = []
        hp_siz_num_list = []
        for node in nodes:
       #     hp_dict = {}
            if node.idrac_ip == None:
                print "idrac_ip not found in node list"
                continue;
            else:
                filename = self.ssh_idrac(node.idrac_ip,ipmi_user,ipmi_pass)
                memory = self.extract_mem_size(filename)
                os.remove(filename)
                hp_siz_num = self.showlimits(memory)
                hp_node_dit={}
                hp_node_dit[node.idrac_ip]=hp_siz_num
                hp_siz_num_list.append(hp_node_dit)
             #   print hp_siz_num_list
                val = self.compareLimits(hp_siz_num,hp_dic)
             #   hp_dict[node[0]["idrac_ip"]] = dic
                val_list.append(val)
             #   hp_list.append(hp_dict)
           # print hp_dic,hp_siz_num_list,val_list
        return hp_siz_num_list,val_list
    
    def get_key_value_from_section(self,key_value_dict,desired_key):
        missing="Value Missing"
     #   print desired_key.lower()
        if desired_key.lower() in key_value_dict:
          #  print desired_key.lower(), key_value_dict[desired_key.lower()]
            return str(key_value_dict[desired_key.lower()])
        else:
            return missing
            
            
    def extract_section(self,fil):
        try:
         #   print "reading %s" %fil
            Config = ConfigParser.ConfigParser()
            Config.read(fil)
        except Exception as e:
            print "Error %s"%e
        except (ConfigParser.MissingSectionHeaderError,
                    ConfigParser.ParsingError):
            print "No Section header %s"%e
        
        return Config
#    def verify_controller(self,controller_key_val_dict, ip, usr, pas):
 #       filename = self.ssh_idrac(ip, usr, pas)
  #      controller_key_list = list(controller_key_val_dict.keys())
   #     for key_ind in range(0, len(controller_key_val_dict)):
            
    #        self.verify_platform(filename, controller_key_list[controller_key_list[key_ind.lower()])
     #       self.verify_cpu(filename, controller_key_list[controller_key_list[key_ind.lower()]))
    
    def extract_nics(self,fil):
        Config = self.extract_section(fil)
        # Lists variable initialization
        Nic_section_list, nic_manufac_list, nic_descrp_list, nic_dev_descrp_list, nic_fqdd_list = ([
        ]for i in range(5))
        nic_pci_sub_device_id_list, nic_pci_sub_vendor_id_list, nic_pci_device_id_list = (
            []for i in range(3))
        nic_pci_vendor_id_list, nic_bus_no_list, nic_slot_typ_list, nic_data_bus_width_list = ([
        ]for i in range(4))
        nic_fun_no_list, nic_dev_no_list = ([]for i in range(2))
        # Store nic sections into the list
        for s in Config.sections():
            if "InstanceID: NIC" in s:
                Nic_section_list += [s]
        Nic_set = set()
        port_slots = len(Nic_section_list)
        for section in Nic_section_list:
            nic = section.split(" ")[1].split(".")[0] + "." + section.split(" ")[1].split(
                ".")[1] + "." + section.split(" ")[1].split(".")[2].split("-")[0]
            if nic not in Nic_set:
                Nic_set.add(nic)
        nic_slots = len(Nic_set)
        # Using the set of nics, make a dictionary which corresponds to the ports each nic contains
        Nic_set_dic = dict()
        for nic in Nic_set:
            for nic_sec in Nic_section_list:
                if nic in nic_sec:
                    if nic not in Nic_set_dic:
                        Nic_set_dic[nic] = list()
                        Nic_set_dic[nic].append(nic_sec)
                    else:
                        Nic_set_dic[nic].append(nic_sec)

            # Extract key, values from nic sections
        for nic_sec in Nic_section_list:
            key_valu_dict  = dict(Config.items(nic_sec))
            nic_manufac_list += [self.get_key_value_from_section(key_valu_dict, 'Manufacturer')]
            nic_descrp_list += [self.get_key_value_from_section(key_valu_dict, 'Description')]
            nic_dev_descrp_list += [self.get_key_value_from_section(key_valu_dict,
                                               'DeviceDescription')]
            nic_fqdd_list += [self.get_key_value_from_section(key_valu_dict, 'FQDD')]
            nic_pci_sub_device_id_list += [
                self.get_key_value_from_section(key_valu_dict, 'PCISubDeviceID')]
            nic_pci_sub_vendor_id_list += [
                self.get_key_value_from_section(key_valu_dict, 'PCISubVendorID')]
            nic_pci_device_id_list += [self.get_key_value_from_section(key_valu_dict, 'PCIDeviceID')]
            nic_pci_vendor_id_list += [self.get_key_value_from_section(key_valu_dict, 'PCIVendorID')]
            nic_bus_no_list += [self.get_key_value_from_section(key_valu_dict, 'BusNumber')]
            nic_slot_typ_list += [self.get_key_value_from_section(key_valu_dict, 'SlotType')]
            nic_data_bus_width_list += [
                self.get_key_value_from_section(key_valu_dict, 'DataBusWidth')]
            nic_fun_no_list += [self.get_key_value_from_section(key_valu_dict, 'FunctionNumber')]
            nic_dev_no_list += [self.get_key_value_from_section(key_valu_dict, 'DeviceNumber')]

        nic_info_dictionaries = [dict() for x in range(port_slots)]
        # Store nic key value individually into the list of dictionaries
        for i in range(port_slots):
            nic_info_dictionaries[i]['manufacturer'] = nic_manufac_list[i]
            nic_info_dictionaries[i]['decription'] = nic_descrp_list[i]
            nic_info_dictionaries[i]['device_description'] = nic_dev_descrp_list[i]
            nic_info_dictionaries[i]['fqdd'] = nic_fqdd_list[i]
            nic_info_dictionaries[i]['pci_subdevice_id'] = nic_pci_sub_device_id_list[i]
            nic_info_dictionaries[i]['pci_Subvendor_id'] = nic_pci_sub_vendor_id_list[i]
            nic_info_dictionaries[i]['pci_Dev_id'] = nic_pci_device_id_list[i]
            nic_info_dictionaries[i]['pci_vendor_id'] = nic_pci_vendor_id_list[i]
            nic_info_dictionaries[i]['bus_number'] = nic_bus_no_list[i]
            nic_info_dictionaries[i]['slot_type'] = nic_slot_typ_list[i]
            nic_info_dictionaries[i]['data_bus_width'] = nic_data_bus_width_list[i]
            nic_info_dictionaries[i]['function_number'] = nic_fun_no_list[i]
            nic_info_dictionaries[i]['dev_number'] = nic_dev_no_list[i]
            # Store keys and values of nic in dictionary using a nic set vs port formate
        nic_port_dictionaries = dict()
        nic_name_list = []
        for nic in Nic_set:
            nic_name_list.append(nic)
            dumy_dict = [dict() for x in range(len(Nic_set_dic[nic]))]
            ind = 0
            for nics in Nic_set_dic[nic]:
                for j in range(port_slots):
                    if nic_info_dictionaries[j]['fqdd'] in nics:
                        dumy_dict[ind] = nic_info_dictionaries[j]
                        ind += 1
            nic_port_dictionaries[nic] = dumy_dict
        nic_model= ""
        for nicslot in Nic_set:
     #       print nicslot, nic_port_dictionaries[nicslot][0]['decription']
            nic_model+= nic_port_dictionaries[nicslot][0]['decription']
            nic_model+= ", "
    #    print nic_slots, nic_name_list, port_slots, nic_port_dictionaries
        return nic_slots, nic_name_list, port_slots, nic_port_dictionaries,nic_model


    def extract_cpu(self,fil):
        Config = self.extract_section(fil)
        Cpu_section_list, cpu_processor_list, cpu_family_list, cpu_manufac_list, cpu_curr_clock_list, cpu_model_list = ([
        ]for i in range(6))
        cpu_prim_status_list, cpu_virt_list, cpu_voltag_list, cpu_enabled_thread_list, cpu_max_clock_speed_list = ([
        ]for i in range(5))
        cpu_ex_bus_clock_speed_list, cpu_hyper_thread_list, cpu_status_list = (
            []for i in range(3))

        # Store cpu sections into the list
        for s in Config.sections():
            if "InstanceID: CPU.Socket" in s:
                Cpu_section_list += [s]
        for cpu_sec in Cpu_section_list:
            key_valu_dict = dict(Config.items(cpu_sec))
            
            cpu_processor_list += [self.get_key_value_from_section(key_valu_dict,
                                              'NumberOfProcessorCores')]
            cpu_family_list += [self.get_key_value_from_section(key_valu_dict, 'CPUFamily')]
            cpu_manufac_list += [self.get_key_value_from_section(key_valu_dict, 'Manufacturer')]
            cpu_curr_clock_list += [self.get_key_value_from_section(key_valu_dict,
                                               'CurrentClockSpeed')]
            cpu_model_list += [self.get_key_value_from_section(key_valu_dict, 'Model')]
            cpu_prim_status_list += [self.get_key_value_from_section(key_valu_dict, 'PrimaryStatus')]
            cpu_virt_list += [self.get_key_value_from_section(key_valu_dict,
                                         'VirtualizationTechnologyEnabled')]
            cpu_voltag_list += [self.get_key_value_from_section(key_valu_dict, 'Voltage')]
            cpu_enabled_thread_list += [self.get_key_value_from_section(key_valu_dict, 'NumberOfEnabledThreads')]
            cpu_max_clock_speed_list += [
                self.get_key_value_from_section(key_valu_dict, 'MaxClockSpeed')]
            cpu_ex_bus_clock_speed_list += [self.get_key_value_from_section(key_valu_dict, 'ExternalBusCLockSpeed')]
            cpu_hyper_thread_list += [self.get_key_value_from_section(key_valu_dict,
                                                 'HyperThreadingEnabled')]
            cpu_status_list += [self.get_key_value_from_section(key_valu_dict, 'CPUStatus')]
            
        cpu_slots = len(cpu_processor_list)
        cpu_info_dictionaries = [dict() for x in range(cpu_slots)]
        cpu_info_list = []
        total_threads = 0
        # Store cpu key value individually into the list of dictionaries
        for i in range(cpu_slots):
            cpu_info_dictionaries[i]['no_of_processors'] = cpu_processor_list[i]
            cpu_info_dictionaries[i]['cpu_family'] = cpu_family_list[i]
            cpu_info_dictionaries[i]['manufacturer'] = cpu_manufac_list[i]
            cpu_info_dictionaries[i]['current_clock_speed'] = cpu_curr_clock_list[i]
            cpu_info_dictionaries[i]['model'] = cpu_model_list[i]
            cpu_info_dictionaries[i]['primary_status'] = cpu_prim_status_list[i]
            cpu_info_dictionaries[i]['virtualization_technology_enabled'] = cpu_virt_list[i]
            cpu_info_dictionaries[i]['voltage'] = cpu_voltag_list[i]
            cpu_info_dictionaries[i]['no_of_enabled_thread'] = cpu_enabled_thread_list[i]
            cpu_info_dictionaries[i]['max_clock_Speed'] = cpu_max_clock_speed_list[i]
            cpu_info_dictionaries[i]['external_bus_clock_speed'] = cpu_ex_bus_clock_speed_list[i]
            cpu_info_dictionaries[i]['hyper_threading_enabled'] = cpu_hyper_thread_list[i]
            total_threads += int(cpu_enabled_thread_list[i])
            cpu_info_dictionaries[i]['cpu_status'] = cpu_status_list[i]
            # Store list of dictionaries into a list
        cpu_info_list = cpu_info_dictionaries
        if cpu_slots == 2:
            if cpu_info_dictionaries[0]['model'] == cpu_info_dictionaries[1]['model']:
                common_cpu = (cpu_info_dictionaries[0]['model'].split(" ")[3])
                commmon_speed = cpu_info_dictionaries[0]['model'].split("@")[1]
                cpu_ver = (cpu_info_dictionaries[0]['model'].split(" ")[4])
#                cpu_ver =  cpu_info_dictionaries[0]['model'].split(" ")[1].split(" ")[1].split(" ")[1].split(" ")[1].split(" ")[0]
       # print cpu_slots, total_threads, cpu_info_list
        return cpu_slots, total_threads, cpu_info_list, common_cpu,commmon_speed,cpu_ver

    def extract_hard_drives(self,fil):
        Config = self.extract_section(fil)
        # Lists variable initialization
        Drive_section_list, driv_dev_list, driv_dev_descrp_list, driv_ppid_list, temp_size_list, = ([
        ]for i in range(5))
        driv_sas_address_list, driv_max_cap_speed_list, driv_used_siz_byte_list, driv_media_typ_list = ([
        ]for i in range(4))
        driv_blck_siz_byte_list, driv_bus_protocol_list, driv_serial_no_list, driv_manufacturer_list = ([
        ]for i in range(4))
        driv_fqdd_list, driv_slot_list, driv_raid_status_list, driv_predictiv_fail_status_list, driv_free_siz_byte_list, driv_total_siz_list = ([
        ]for i in range(6))
        # Store drive sections into the list
        for s in Config.sections():
            if "InstanceID: Disk" in s:
                if ("Virtual" in s) or ("FlashCard" in s):
                    continue;
                else:
                    Drive_section_list += [s]
                    
        drive_list_len = len(Drive_section_list)
        
        # Extract key, values from drives sections
        check_ssd = 0
        check_hdd = 0
        for dev_sec in Drive_section_list:
            key_valu_dict = dict(Config.items(dev_sec))
            driv_dev_list += [self.get_key_value_from_section(key_valu_dict, 'Device Type')]
            driv_dev_descrp_list += [self.get_key_value_from_section(key_valu_dict,
                                                'DeviceDescription')]
            driv_ppid_list += [self.get_key_value_from_section(key_valu_dict, 'PPID')]
            driv_sas_address_list += [self.get_key_value_from_section(key_valu_dict, 'SASAddress')]
            driv_max_cap_speed_list += [
                self.get_key_value_from_section(key_valu_dict, 'MaxCapableSpeed')]
            driv_used_siz_byte_list += [
                self.get_key_value_from_section(key_valu_dict, 'UsedSizeInBytes')]
            driv_free_siz_byte_list += [
                self.get_key_value_from_section(key_valu_dict, 'FreeSizeInBytes')]
            total_hard_size = int(self.get_key_value_from_section(key_valu_dict, 'UsedSizeInBytes').split(" ")[0]) + int(
                self.get_key_value_from_section(key_valu_dict, 'FreeSizeInBytes').split(" ")[0])
            total_hard_size /= math.pow(1024, 3)
    #	    print total_hard_size
            driv_total_siz_list.append(total_hard_size)
            driv_media_typ_list += [self.get_key_value_from_section(key_valu_dict, 'MediaType')]
            # check and count the total ssd or hdd
            if ("Solid State Drive" in self.get_key_value_from_section(key_valu_dict, 'MediaType')):
                check_ssd += 1
            if ("HDD" in self.get_key_value_from_section(key_valu_dict, 'MediaType') or ("Magnetic Drive" in self.get_key_value_from_section(key_valu_dict, 'MediaType'))):
                check_hdd += 1
            driv_blck_siz_byte_list += [
                self.get_key_value_from_section(key_valu_dict, 'BlockSizeInBytes')]
            driv_bus_protocol_list += [self.get_key_value_from_section(key_valu_dict, 'BusProtocol')]
            driv_serial_no_list += [self.get_key_value_from_section(key_valu_dict, 'SerialNumber')]
            driv_manufacturer_list += [
                self.get_key_value_from_section(key_valu_dict, 'Manufacturer')]
            driv_fqdd_list += [self.get_key_value_from_section(key_valu_dict, 'FQDD')]
            driv_slot_list += [self.get_key_value_from_section(key_valu_dict, 'Slot')]
            driv_raid_status_list += [self.get_key_value_from_section(key_valu_dict, 'RaidStatus')]
            driv_predictiv_fail_status_list += [
                self.get_key_value_from_section(key_valu_dict, 'PredictiveFailureState')]
            
    #        print driv_total_siz_list
        total_size = str(sum([int(x) for x in driv_total_siz_list])*1024) + " MB"
        driv_slots = len(Drive_section_list)
        
        # list of dictionaries for hdd and ssd for storing each slot information seperately
        driv_info_hdd_dictionaries = [dict() for x in range(check_hdd)]
        driv_info_ssd_dictionaries = [dict() for x in range(check_ssd)]
        driv_info_list = []
        # Store hardrive key value individually into the list of dictionaries
        hdd_index = 0
        ssd_index = 0
        for i in range(driv_slots):
            if "HDD" in driv_media_typ_list[i] or "Magnetic Drive" in driv_media_typ_list[i]:
                driv_info_hdd_dictionaries[hdd_index]['device_type'] = driv_dev_list[i]
                driv_info_hdd_dictionaries[hdd_index]['device_description'] = driv_dev_descrp_list[i]
                driv_info_hdd_dictionaries[hdd_index]['ppid'] = driv_ppid_list[i]
                driv_info_hdd_dictionaries[hdd_index]['sas_address'] = driv_sas_address_list[i]
                driv_info_hdd_dictionaries[hdd_index]['max_capable_speed'] = driv_max_cap_speed_list[i]
                driv_info_hdd_dictionaries[hdd_index]['used_size_in_bytes'] = driv_used_siz_byte_list[i]
                driv_info_hdd_dictionaries[hdd_index]['free_size_in_bytes'] = driv_free_siz_byte_list[i]
                driv_info_hdd_dictionaries[hdd_index]['total_size_in_giga_bytes'] = str(
                    driv_total_siz_list[i]) + " GB"
    #		    driv_info_hdd_dictionaries[hdd_index]['media_type'] = driv_media_typ_list[i]
                driv_info_hdd_dictionaries[hdd_index]['block_size_in_bytes'] = driv_blck_siz_byte_list[i]
                driv_info_hdd_dictionaries[hdd_index]['bus_protocol'] = driv_bus_protocol_list[i]
                driv_info_hdd_dictionaries[hdd_index]['serial_no'] = driv_serial_no_list[i]
                driv_info_hdd_dictionaries[hdd_index]['manufacturer'] = driv_manufacturer_list[i]
                driv_info_hdd_dictionaries[hdd_index]['fqdd'] = driv_fqdd_list[i]
                driv_info_hdd_dictionaries[hdd_index]['slot'] = driv_slot_list[i]
                driv_info_hdd_dictionaries[hdd_index]['raid_status'] = driv_raid_status_list[i]
                driv_info_hdd_dictionaries[hdd_index]['predictive_failure_state'] = driv_predictiv_fail_status_list[i]
                hdd_index += 1
            elif "Solid State Drive" in driv_media_typ_list[i]:
                driv_info_ssd_dictionaries[ssd_index]['device_type'] = driv_dev_list[i]
                driv_info_ssd_dictionaries[ssd_index]['device_description'] = driv_dev_descrp_list[i]
                driv_info_ssd_dictionaries[ssd_index]['ppid'] = driv_ppid_list[i]
                driv_info_ssd_dictionaries[ssd_index]['sas_address'] = driv_sas_address_list[i]
                driv_info_ssd_dictionaries[ssd_index]['max_capable_speed'] = driv_max_cap_speed_list[i]
                driv_info_ssd_dictionaries[ssd_index]['used_size_in_bytes'] = driv_used_siz_byte_list[i]
                driv_info_ssd_dictionaries[ssd_index]['free_size_in_bytes'] = driv_free_siz_byte_list[i]

                driv_info_ssd_dictionaries[ssd_index]['total_size_in_giga_bytes'] = str(
                    driv_total_siz_list[i]) + " GB"
    #		    driv_info_ssd_dictionaries[ssd_index]['media_type'] = driv_media_typ_list[i]
                driv_info_ssd_dictionaries[ssd_index]['block_size_in_bytes'] = driv_blck_siz_byte_list[i]
                driv_info_ssd_dictionaries[ssd_index]['bus_protocol'] = driv_bus_protocol_list[i]
                driv_info_ssd_dictionaries[ssd_index]['serial_no'] = driv_serial_no_list[i]
                driv_info_ssd_dictionaries[ssd_index]['manufacturer'] = driv_manufacturer_list[i]
                driv_info_ssd_dictionaries[ssd_index]['fqdd'] = driv_fqdd_list[i]
                driv_info_ssd_dictionaries[ssd_index]['slot'] = driv_slot_list[i]
                driv_info_ssd_dictionaries[ssd_index]['raid_status'] = driv_raid_status_list[i]
                driv_info_ssd_dictionaries[ssd_index]['predictive_failure_state'] = driv_predictiv_fail_status_list[i]
                ssd_index += 1

        driv_dict = dict()
        driv_type_dict = dict()

        if check_ssd > 0:
            # save ssd dictionaries features into a dictionary
            driv_dict['SSD'] = driv_info_ssd_dictionaries
            # save drives type vs total drive of that type "ssd" into a dictioanary
            driv_type_dict['SSD'] = ssd_index
        if check_hdd > 0:
            driv_dict['HDD'] = driv_info_hdd_dictionaries
            driv_type_dict['HDD'] = hdd_index
        total_drives = check_ssd + check_hdd
        if check_ssd == 0 and check_hdd !=0:
            driv_bus_type = driv_info_hdd_dictionaries[0]['bus_protocol']
        elif check_ssd != 0 and check_hdd ==0:
            driv_bus_type = driv_info_ssd_dictionaries[0]['bus_protocol']
        elif check_ssd != 0 and check_hdd !=0:
            if driv_info_hdd_dictionaries[0]['bus_protocol'] == driv_info_ssd_dictionaries[0]['bus_protocol']:
                driv_bus_type = driv_info_hdd_dictionaries[0]['bus_protocol']
            else:
                driv_bus_type = driv_info_hdd_dictionaries[0]['bus_protocol']+driv_info_ssd_dictionaries[0]['bus_protocol']
      #  print driv_type_dict, total_size, driv_dict
        return driv_type_dict, total_size, driv_dict, total_drives, driv_bus_type

    def extract_idrac_verion_model(self,fil):
        Config = self.extract_section(fil)
        for s in Config.sections():
            if "InstanceID: System.Embedded" in s:
                self.dictionary['idrac_model'] = Config.get(
                    str(s), 'Model').split(" ")[1]
            elif "InstanceID: iDRAC." in s:
                self.dictionary['idrac'] = Config.get(
                    str(s), 'FirmwareVersion')
                    
    def extract_raid_info(self,fil):
        Config = self.extract_section(fil)
        for s in Config.sections():
            if "InstanceID: RAID.Integrated." in s and "Controller"  in Config.get(s, "Device Type"):
                self.dictionary['raid_model'] = Config.get(
                    str(s), 'ProductName')
                self.dictionary['raid_cache_size'] = Config.get(
                    str(s), 'CacheSizeInMB')
                    
            else:
                self.dictionary['raid_model'] = ""
                self.dictionary['raid_cache_size']= ""
    def extract_mem(self,fil):
        Config = self.extract_section(fil)
        Mem_section_list, mem_size_list, mem_speed_list, mem_descp_list, mem_serial_list, mem_model_list, mem_status_list = ([
        ]for i in range(0, 7))
        for s in Config.sections():
            if "InstanceID: DIMM.Socket" in s:
                Mem_section_list += [s]
     #       Mem_section_list = [s for s, s in enumerate(
      #          Config.sections()) if "InstanceID: DIMM.Socket" in s]
            # Extract key, values from memory sections
        for mem_sec in Mem_section_list:
            key_valu_dict = dict(Config.items(mem_sec))
      #      print key_valu_dict
            mem_size_list += [self.get_key_value_from_section(key_valu_dict, 'Size')]
            mem_speed_list += [self.get_key_value_from_section(key_valu_dict,
                                          'CurrentOperatingSpeed')]
            mem_descp_list += [self.get_key_value_from_section(key_valu_dict, 'Manufacturer')]
            mem_serial_list += [self.get_key_value_from_section(key_valu_dict, 'SerialNumber')]
            mem_model_list += [self.get_key_value_from_section(key_valu_dict, 'Model')]
            mem_status_list += [self.get_key_value_from_section(key_valu_dict, 'PrimaryStatus')]
            # Check the types and sizes of memory, convert it into MB, and store them into a list
        for index in range(0, len(mem_size_list)):
            if "MB" in mem_size_list[index]:
                value = int(mem_size_list[index].replace("MB", ""))
                mem_size_list[index] = value
            elif "PB" in mem_size_list[index]:
                value = mem_size_list[index].replace("PB", "")
                value *= math.pow(1024, 3)
                mem_size_list[index] = value
            elif "TB" in mem_size_list[index]:
                value = mem_size_list[index].replace("TB", "")
                value *= math.pow(1024, 2)
                mem_size_list[index] = value
            elif "GB" in mem_size_list[index]:
                value = mem_size_list[index].replace("GB", "")
                value *= math.pow(1024, 1)
                mem_size_list[index] = value
            elif "KB" in mem_size_list[index]:
                value = mem_size_list[index].replace("KB", "")
                value /= float(1024)
                mem_size_list[index] = value
            # total memory slots
        mem_slots = len(mem_size_list)
        # list of dictionaries for storing features of each memory slot
        mem_info_dictionaries = [dict() for x in range(mem_slots)]
        mem_info_list = []

        # Store memory key value individually intothe list of dictionaries
        for i in range(mem_slots):
            mem_info_dictionaries[i]['manufacturer'] = mem_descp_list[i]
            mem_info_dictionaries[i]['speed'] = mem_speed_list[i]
            mem_info_dictionaries[i]['model'] = mem_model_list[i]
            mem_info_dictionaries[i]['serial'] = mem_serial_list[i]
            mem_info_dictionaries[i]['status'] = mem_status_list[i]
        # Store list of dictionaries into a list
        mem_info_list = mem_info_dictionaries
        total_mem = str(sum([int(x) for x in mem_size_list])*1024)+ " MB"
    #    print total_mem, mem_info_list, mem_slots
        return total_mem, mem_info_list, mem_slots

    def extact_info(self,ip, usr, pas):
        
        filename = self.ssh_idrac(ip, usr, pas)
        if filename== False:
           # print "SSH did not work"
            return False
      #  controller_dic = OrderedDict()
        tot_mem, mem_info, mslots= self.extract_mem(filename)

        self.extract_idrac_verion_model(filename)
        self.dictionary['total_memory_size'] = tot_mem
        self.dictionary['total_memory_slots'] = str(mslots)
        driv_type, tot_driv_siz, driv_info, total_drives,bus_typ = self.extract_hard_drives(filename)
        self.dictionary['total_drives_size'] = tot_driv_siz
        self.dictionary['total_drives'] = str(total_drives)
        self.dictionary['drive_bus_type'] = str(bus_typ)
        
        cslots, threads, cpu_info,comm_cpu, comm_speed,cpu_ver = self.extract_cpu(filename)
  #      print comm_cpu, comm_speed,cpu_ver
        self.dictionary['total_cpu'] = str(cslots)
        self.dictionary['cpu'] = comm_cpu
        self.dictionary['cpu_speed'] = comm_speed
        self.dictionary['cpu_version'] = cpu_ver
        nslots, nics_name_list, ports_slot, nic_info,nic_mod = self.extract_nics(filename)
        self.dictionary['nic_slots'] =nslots
        self.dictionary['nics'] = nic_mod
        self.extract_raid_info(filename)
#        self.dictionary['nic_name'] = nics_name_list
 #       self.dictionary['ports_slot'] = ports_slot
  #      self.dictionary['nic_info'] = nic_info

        #   self.dictionary['cpu_threads'] = threads
     #   self.dictionary['cpu_info'] = cpu_info
      #  self.dictionary['mem_slot'] = mslots

      #  self.dictionary['mem_info'] = mem_info
     #   cslots, threads, cpu_info = self.extract_cpu(filename)
     #   self.dictionary['cpu1'] = cpu_info
     #   self.dictionary['cpu_threads'] = threads
     #   self.dictionary['cpu_info'] = cpu_info
     #   nslots, nics_name_list, ports_slot, nic_info = self.extract_nics(filename)
     #  self.dictionary['nic_slot'] = nslots
    #   self.dictionary['nic_name'] = nics_name_list
    #   self.dictionary['ports_slot'] = ports_slot
     #   self.dictionary['nic_info'] = nic_info
        
        
        
        dumy_list = []
        dumy_list.append(self.dictionary)
     #   self.dictionary = controller_dic
#        list.extend(mslots,threads,cpu_info,nslots,nics_name_list,ports_slot,nic_info,driv_type,tot_driv_siz,driv_info)
        os.remove(filename)
        return True
       # timestr = time.strftime("%Y%m%d_%H%M%S")
       # Outfilename = "Controller" + "_" + timestr + ".ini"
       # fptr = open(Outfilename, "w+")
       # json.dump(dumy_list, fptr, indent=4,
       # sort_keys=False, separators=(',', ':'))
       # fptr.close()
       # return Outfilename
    #    return controller_dic
                
    def compare_values(self,control_dict,typ):
        control_keys = list(control_dict.keys())
        extrctd_idrac_keys = list(self.dictionary.keys())
   #     print control_dict
    #    print self.dictionary
      #  diffkeys = [k for k in control_dict if control_dict[k] != self.dictionary[k]]
     #   for loop in range(0, len(control_dict)):
        try:
     #       print "Table"
            table = PrettyTable()
#           table.field_names = ["Type","iDRAC Model","CPU Model","CPU Version","CPU Speed","Total CPU","Total Memory Size","Total Memory Slots","Total Drives Size","Total Drive Slot","Drive Bus Type","Total NIC Slots","NICs"] 
            table.add_column("Type",["iDRAC Model","CPU Model","CPU Version","CPU Speed","Total CPU","Total Memory Size","Total Memory Slots","Total Drives Size","Total Drive Slot","Drive Bus Type","Total NIC Slots","NICs"])
            table.add_column("Required",[control_dict['idrac_model'],control_dict['cpu'],control_dict['cpu_version'],control_dict['cpu_speed'],int(control_dict['total_cpu']),control_dict['total_memory_size'],control_dict['total_memory_slots'],control_dict['total_drives_size'],control_dict['total_drives'],control_dict['drive_bus_type'],control_dict['nic_slots'],control_dict['nics']])
            table.add_column("Available"+typ,[self.dictionary['idrac_model'],self.dictionary['cpu'],self.dictionary['cpu_version'],self.dictionary['cpu_speed'],int(self.dictionary['total_cpu']),self.dictionary['total_memory_size'],self.dictionary['total_memory_slots'],self.dictionary['total_drives_size'],self.dictionary['total_drives'],self.dictionary['drive_bus_type'],self.dictionary['nic_slots'],self.dictionary['nics']])            
            
 #           pass
            if control_dict['idrac_model'] in self.dictionary['idrac_model']:
                mod="Yes"
                pass
            else: 
                mod="No"
#                print "Idrac model not matched"
            if control_dict['cpu'] in self.dictionary['cpu']:
                cpu="Yes"
                pass
            else:
                cpu="No"
            if control_dict['cpu_version'] in self.dictionary['cpu_version']:
                cpu_ver="Yes"
                pass 
            else:
                cpu_ver="No"
            if control_dict['cpu_speed'] in self.dictionary['cpu_speed']:
                cpu_sp="Yes"
                pass
            else:
                cpu_sp="No"
            if int(control_dict['total_cpu']) <= int(self.dictionary['total_cpu']):
                t_cpu="Yes"
                pass
            else:
                t_cpu="No"
            if int(control_dict['total_memory_size'].split(" ")[0]) <= int(self.dictionary['total_memory_size'].split(" ")[0]):
                t_mem="Yes"
                pass
            else:
                t_mem="No"
            if int(control_dict['total_memory_slots']) <= int(self.dictionary['total_memory_slots']):
                t_mem_sl="Yes"
                pass
            else: 
                t_mem_sl="No"
            if int(control_dict['total_drives']) <= int(self.dictionary['total_drives']):
                t_dr="Yes"
                pass
            else:
                t_dr="No"
            if int(control_dict['total_drives_size'].split(" ")[0]) <= int(self.dictionary['total_drives_size'].split(" ")[0]):
                t_dr_sz="Yes"
                pass
            else:
                t_dr_sz="No"    
            if control_dict['nics'].split(",")[0] in self.dictionary['nics']:
                nic1="Yes |"
                pass
            else:
                nic1="No |"
            if re.search('/([I])\w+',self.dictionary['nics']):
                nic2="Yes"
                pass
            else:
                nic2="No"
            nic = nic1+nic2
            if int(control_dict['nic_slots']) <= int(self.dictionary['nic_slots']):
                nic_sl="Yes"
                pass
            else:
                nic_sl="No"
            if control_dict['drive_bus_type'] in self.dictionary['drive_bus_type']:
                driv_bus="Yes"
                pass
            else:
                driv_bus="No"
#            table.add_column("Result",["yes","yes","yes","yes","yes","yes","yes","yes","yes","yes","yes","yes"]
            table.add_column("Result",[mod,cpu,cpu_ver,cpu_sp,t_cpu,t_mem,t_mem_sl,t_dr_sz,t_dr,driv_bus,nic_sl,nic])
            print table
        except Exception as e:
            print e
            return False
        return True
                
                
   #         if control_dict[k] in self.dictionary[k]:
   #             pass
   #             print k, ':', control_dict[k], '->', self.dictionary[k]
    #        else:
     #           continue
#            print k, ':', control_dict[k], '->', self.dictionary[k]
        #        for ind in range(0, len(control_dict)):
            
    def verify_jetstream(self, filename, nodes, ipmi_user, ipmi_pass):
        print "Node : %s" % nodes  
        typ = False  
        for node in nodes:
            if node.idrac_ip == None:
                print "idrac_ip not found in node list"
                continue;
            else:
                

                Config = self.extract_section(filename)
                
                if node.is_compute == True:
           #         print "****Compute*****"
                    compute_key_val = OrderedDict(Config.items("Compute"))
#                    print compute_key_val
                    typ = self.extact_info(node.idrac_ip ,ipmi_user, ipmi_pass)
                    if typ != False:
                        typ = self.compare_values(compute_key_val," (Compute)")
              #      print self.dictionary;
               
                elif node.is_controller == True:
          #          print "*****Controller*****"
                    controller_key_val = OrderedDict(Config.items("Controller"))
 #                   print controller_key_val
                    typ = self.extact_info(node.idrac_ip ,ipmi_user, ipmi_pass)
                    if typ != False:
                        typ = self.compare_values(controller_key_val," (Controller)")
                    
                elif "Storage" in s:
                    storage_section = OrderedDict(Config.items("Storage"))
                    
                elif node.is_sah == "true":
         #           print "*****SAH******"
                    sah_key_val = OrderedDict(Config.items("SAH"))
  #                  print sah_key_val
                    typ = self.extact_info(node.idrac_ip ,ipmi_user, ipmi_pass)
                    if typ != False:
                        typ = self.compare_values(sah_key_val," (SAH)")
        return typ           
#hwInventory = Inventory()
#Ip = "192.168.2.106"
#Us = "root"
#Pa = "calvin"
#hwInventory.getMem(Ip,Us,Pa)



