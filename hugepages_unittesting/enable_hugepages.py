'''
/************************************************************************
* LEGALESE:   Copyright (c) 2016-2017, Dell EMC
*
* This source code is confidential, proprietary, and contains trade
* secrets that are the sole property of Dell EMC.
* Copy and/or distribution of this source code or disassembly or reverse
* engineering of the resultant object code are strictly forbidden without
* the written consent of Dell EMC.
*
************************************************************************
*
* FILE NAME: enable_hugepages.py
*
* DESCRIPTION
*    The script is responsible for enabling
*    hugepages support on the Dell NFV Platform
*    by making configuration changes in the Compute
*    nodes
*
* ENVIRONMENT
*  Development: Microsoft Windows 10
*  Target: RHEL 7
*
* MODIFICATION HISTORY
* 04-01-2016 version 1.0
* 04-04-2016 version 1.1
* 04-05-2016 version 1.2
* 04-06-2016 version 1.3
* 04-07-2016 version 1.4
* 04-08-2016 version 1.5
* 04-11-2016 version 1.6
* 04-14-2016 version 1.7
* 04-18-2016 version 1.8
* 04-20-2016 version 1.9
* 04-25-2016 version 4.5
* 06-10-2016 version 4.5.1
* 06-20-2016 version 4.5.2
* 06-22-2016 version 4.5.3
* 06-23-2016 version 4.5.4
* 06-29-2016 version 4.5.5
* 07-01-2016 version 4.5.6
* 07-20-2016 version 4.5.7
* 07-22-2016 version 5.0
* 10-07-2016 version 5.1
* 10-10-2016 version 5.2
* 09-11-2016 version 6.1
* 12-14-2016 version 6.2
* 01-12-2017 version 6.3
* 04-18-2017 version 10.0

*************************************************************************/
'''

version = '10.1'

try:
    import string
    import sys
    import argparse
    import os
    import math
    import requests
    import json
    import getpass
    import pwd
    import time
    import re
    import subprocess
    import readline
    import unittest
    import logging as Logger
    from novaclient import client as nvclient
    from urlparse import urlparse
    import paramiko
    from prettytable import PrettyTable
    from collections import OrderedDict
    import pandas as pd
    from tabulate import tabulate
    from hpsrc.ComputeConfig import ComputeConfig
    from hpsrc.GlobVar import GlobVar
    from hpsrc.FlavorControl import FlavorControl
except ImportError as error:
    print "You don't have module  \"{0}\" installed".format(error.message[16:])
    exit()
    

'''
Initializing the Logger
'''
nfv_logger = Logger.getLogger('dell_nfv_logger')


formatter = Logger.Formatter('[DellNFV_enable_hugepages_v' + version +
                             '] %(levelname)s:%(asctime)s:%(message)s')
Logger_format = '[Internal_Library_Log] %(levelname)s:%(asctime)s:%(' \
                'message)s'
console_handler = Logger.StreamHandler()
console_handler.setLevel(Logger.INFO)
console_handler.setFormatter(formatter)
nfv_logger.addHandler(console_handler)
Logger.basicConfig(format=Logger_format, level=Logger.INFO)


'''
Class responsible for parsing and storing
command line arguments for the hugepages
script
'''


class ArgumentParser:

    __flavor_name = ""
    __hpgsize = 0
    __hpgnum = 0
    __hostos_memcap = 0
    __host_memcap_extra = 0

    __action = ""
    __scope = ""
    __logfile = ""

    __flavor_metadata = {}

    __undercloud_username = ""
    __undercloud_password = ""
    __authentication_url = ""
    __remove_flavor = False

    def __init__(self, glob):
        self.glob = glob
    
    def getFlavorName(self):
        return self.flavor_name

    def getHpgSize(self):
        return self.hpgsize

    def getHpgNum(self):
        return self.hpgnum

    def getHostMemcap(self):
        return self.hostos_memcap

    def getHostMemCapExtra(self):
        return self.host_memcap_extra

    def getAction(self):
        return self.action

    def getScope(self):
        return self.scope

    def getLogFile(self):
        return self.logfile

    def getFlavorMetadata(self):
        return self.flavor_metadata

    def getUndercloudUsername(self):
        return self.undercloud_username

    def getUndercloudPassword(self):
        return self.undercloud_password

    def getAuthenticationUrl(self):
        return self.authentication_url

    def getRemoveFlavor(self):
        return self.remove_flavor

    def getDirectorInstallUser(self):
        return self.director_install_user

    def calculate_size(self, size):
        sizeunit = size[-2:]
        if sizeunit == 'GB':
            return 1024 * 1024 * int(size[:-2])
        elif sizeunit == 'MB':
            return 1024 * int(size[:-2])

    def extractData(self, record, last=False):
        records = []
        for ind, hpg in enumerate(record['HPG']):
            if ind == 0:
                records.append(('', '', '', hpg['Size'], hpg['Num']))
                continue

            records.append(
                (record['Name'],
                 record['IP'],
                    record['Memory'],
                    '----------',
                    '----------'))
            records.append(('', '', '', hpg['Size'], hpg['Num']))
        if not last:
            records.append(
                ('*******************',
                 '*******************',
                 '********************************',
                 '**********',
                 '**********'))
        return records

    def visualizeJson(self, filename, bool):
        data = pd.read_json(filename)
        records = []
        for i, r in enumerate(data.iterrows()):
            if i == len(data) - 1:
                records += self.extractData(r[1].to_dict(), True)
            else:
                records += self.extractData(r[1].to_dict())
        if bool:
            print tabulate(records, headers=('Name', 'IP', 'Memory available for Hugepages', 'HPGSize', 'HPGNum'), tablefmt='psql')

    def recordLimit(self, nodes_data):
        mbNum = nodes_data[0]["HPG"][0]["Num"]
        gbNum = nodes_data[0]["HPG"][1]["Num"]

        # Iterate all node sizes and find min max for each size & num
        max2MBPages = int(mbNum)
        max1GBPages = int(gbNum)
        min2MBPages = 0
        min1GBPages = 0
        for node in nodes_data:

            for sizeConfig in node['HPG']:
                if sizeConfig['Size'] == "2MB":
                    if sizeConfig['Num'] < max2MBPages:
                        max2MBPages = sizeConfig['Num']
                if sizeConfig['Size'] == "1GB":
                    if sizeConfig['Num'] < max1GBPages:
                        max1GBPages = sizeConfig['Num']

        if max2MBPages >= 1:
            min2MBPages = 1
        else:
            min2MBPages = 0
        if max1GBPages >= 1:
            min1GBPages = 1
        else:
            min1GBPages = 0

        self.Max2MB = max2MBPages
        self.Min2MB = min2MBPages
        self.Max1GB = max1GBPages
        self.Min1GB = min1GBPages
        self.default2MB = glob.DEFAULT_2MB
        self.default1GB = glob.DEFAULT_1GB

        jData = {}
        jData['Max2MB'] = str(max2MBPages)
        jData['Min2MB'] = str(min2MBPages)
        jData['Max1GB'] = str(max1GBPages)
        jData['Min1GB'] = str(min1GBPages)

        #jFileData = json.loads(jData,object_pairs_hook=OrderedDict)
        with open('ConfigurationLimit.json', 'w') as outfile:
            json.dump(
                jData,
                outfile,
                indent=4,
                sort_keys=False,
                separators=(
                    ',',
                    ':'))
        return jData

    def convertSize(self, size):
        if (size == 0):
            return '0B'
        size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size, 1024)))
        p = math.pow(1024, i)
        s = round(size / p, 2)
        return '%s %s' % (s, size_name[i])

    def showlimits(self, bool):
        nodeInfo = []
        get_nodes(args.getUndercloudUsername(), args.getUndercloudPassword(),
                  args.getAuthenticationUrl())

        for i in glob.nodes['compute'].keys():
            computeconfig = ComputeConfig(i, glob.nodes['compute'][i]['ip'],
                                          glob.nodes['compute'][i]['name'],glob)
            glob.nodes['compute'][i]['object'] = computeconfig
            ssh_c = glob.nodes['compute'][i]['object'].ssh_connect()
            if ssh_c is True:

                nfv_logger.info('Fetching memory details from ' 
                                + glob.nodes['compute'][i]['name'])
                memory_check_command = "dmidecode -t memory 17 | grep MB"
                ssh_stderr, ssh_stdout = glob.nodes['compute'][i]['object'].execute_command(
                                         memory_check_command)
                host_total_memory = 0
                for line in ssh_stdout:
                    output = line.split()[1]
                    if output.isdigit():
                        host_total_memory += int(output)
                
                hpgsizes = {"1GB", "2MB"}
                memcapsize = int(self.getHostMemcap()) + \
                    int(self.getHostMemCapExtra())
                # Since command memory_check_command_new displays size in MB's
                # to convert this size into KB it needs to be multiplied with
                # 1024
                freeMem = ((int(host_total_memory) * 1024) - memcapsize)
                TempfreeMem = self.convertSize(freeMem)
                glob.nodes['compute'][i]['object'].setMemory(TempfreeMem)
                dict_node = {}
                dict_node['Name'] = str(glob.nodes['compute'][i]['name'])
                dict_node['IP'] = str(glob.nodes['compute'][i]['ip'])
                dict_node['Memory'] = str(glob.nodes['compute'][i]['object'].getMemory())
                list = []
                for hpgsize in hpgsizes:
                    hugepagesize = self.calculate_size(hpgsize)
                    hpgnum = freeMem / hugepagesize
                    sc = {}
                    sc['Size'] = hpgsize
                    sc['Num'] = hpgnum
                    list.append(sc)
                dict_node['HPG'] = list
                i += 1
                nodeInfo.append(dict_node)
                

            else:
                nfv_logger.warning('Compute' + glob.nodes['compute'][i]['name'] +
                                   ' is not available; '
                                   'could not do Memory sanity check.')
                nfv_logger.error('Aborting the operation. Check log for details.')
                exit(1)

        with open('NodeLimits.json', 'w') as outfile:
            json.dump(
                nodeInfo,
                outfile,
                indent=4,
                sort_keys=False,
                separators=(',', ':'))

        if(bool):
            print "\033[38;5;2m\n\n\nNode Limits:\033[0m"
            print("Name:   Name of compute-node  e.g compute-node-0")
            print("IP:     IP address of compute-node e.g 10.148.44.71")
            print("Memory: Memory on compute node in GBs e.g 3145278MB")
            print("Size:   Hugepages size to be that can be configured on"
                  "any compute-node e.g 1GB,2MB")
            print("Num:    Hugepages number that can be configured with "
                  "respect to Hugepage size e.g 96,49152")

        self.visualizeJson('NodeLimits.json', bool)
        jsonData = self.recordLimit(nodeInfo)
        self.NodeLimits = jsonData

        if(bool):
            print ("\033[38;5;2m\n\n\nConfiguration Limits:\033[0m")
            print ("The table below displays the Max, Min and Default "
                   "Hugepages configuration that can be enabled on all nodes.")
            table = PrettyTable()
            table.field_names = ["HPGSize", "HPGNum Max", "HPGNum Default"]

            default2MB = glob.DEFAULT_2MB
            default1GB = glob.DEFAULT_1GB

            table.add_row(["2MB", jsonData["Max2MB"], default2MB])
            table.add_row(["1GB", jsonData["Max1GB"], default1GB])
            print table

    def read_args_hugepages(self, args):
        sys.argv = args
        self.host_memcap_extra = 4194304  # 4GB = 4194304 KB

        parser = argparse.ArgumentParser(
            description='Enable Huge Pages in Dell NFV Platform',
            add_help=False)
        required_group = parser.add_argument_group('Required Parameters')
        optional_group = parser.add_argument_group('Optional Parameters')
        optional_group.add_argument("-h", "--help", action="help",
                                    help="show this help message and exit")
        optional_group.add_argument("--director_install_user",
                                    help="User for undercloud/overcloud installation",
                                    default="osp_admin")

        mutually_exclusive_group = required_group.add_mutually_exclusive_group(
                                   required=True)
        mutually_exclusive_group.add_argument("--show_limits",
                                              action="store_true",
                                              help="Show Hugepages configuration limits for each  compute node")
        mutually_exclusive_group.add_argument("--flavor_name", 
                                              help="name of flavor to be created")

        optional_group.add_argument("--hpgsize", help="size of hugepage(s) '<size>MB/GB'",
                                    choices=["2MB", "1GB"])
        optional_group.add_argument("--hpgnum", type=int, 
                                    help="number of hugepage(s)")
        optional_group.add_argument("--hostos_memcap",
                                    help="size of memory for host OS '<size>MB/GB'",
                                    default="8GB")
        optional_group.add_argument("--action",
                                    help="set or remove the custom flavor",
                                    choices=["set", "remove"], default="set")
        optional_group.add_argument("--scope",
                                    help="specify compute nodes to turn hugepages on",
                                    choices=["all_compute_nodes"],
                                    default="all_compute_nodes")
        optional_group.add_argument("--logfile",
                                    help="name of the logfile",
                                    default="stdout")
        optional_group.add_argument("--debug",
                                    action="store_true",
                                    help="Increase output verbosity")
        optional_group.add_argument("--remove_flavor",
                                    action="store_true",
                                    help="Flag to remove flavor")

        args = parser.parse_args()

        self.director_install_user = args.director_install_user
        authenticate_undercloud(self.director_install_user)
        self.undercloud_username = glob.UnderCloud_USERNAME
        self.undercloud_password = glob.UnderCloud_PASSWORD
        self.authentication_url = glob.UnderCloud_AUTH_URL

        if args.logfile:
            allowed_logfile_name = set(string.ascii_lowercase +
                                       string.ascii_uppercase +
                                       string.digits +
                                       '.' + '_' + '-' + ',' + '/')
            forbidden_logfile_name = set('.' + '_' + '-' + ',' + '/'+'`')
            if not (set(args.logfile) <= forbidden_logfile_name) and set(args.logfile) <= allowed_logfile_name:
                self.logfile = args.logfile

            else:
                nfv_logger.error(args.logfile + " :Not a valid name for --logfile.")
                exit(1)
        
        

        
        
        if self.getLogFile() != 'stdout':
            file_handler = Logger.FileHandler(self.getLogFile())
            if args.debug:
                nfv_logger.setLevel(Logger.DEBUG)
                file_handler.setLevel(Logger.DEBUG)
            else:
                nfv_logger.setLevel(Logger.INFO)
                file_handler.setLevel(Logger.INFO)

            file_handler.setFormatter(formatter)
            nfv_logger.addHandler(file_handler)
            Logger.basicConfig(format=Logger_format,
                               filename=self.getLogFile(),
                               level=Logger.INFO)

            
        if args.debug:
            nfv_logger.setLevel(Logger.DEBUG)
        else:
            nfv_logger.setLevel(Logger.INFO)
            
        
        if args.hostos_memcap:
            if args.hostos_memcap != "8GB":
                nfv_logger.error(args.hostos_memcap +
                    " :Not a valid value of hostos_memcap."
                    " Valid value is 8GB.")
                exit(1)

            self.hostos_memcap = self.calculate_size(args.hostos_memcap)

        if args.flavor_name:
            allowed_flavor_name = set(string.ascii_lowercase +
                                       string.ascii_uppercase +
                                       string.digits +
                                       '.' + '_' + '-' + ',' + '/')
            forbidden_flavor_name = set('.' + '_' + '-' + ',' + '/'+'`')
            if not (set(args.flavor_name) <= forbidden_flavor_name) and set(args.flavor_name) <= allowed_flavor_name:
                self.flavor_name = args.flavor_name
            else:
                nfv_logger.error(args.flavor_name + " :Not a valid name for --flavor_name.")
                exit(1)

        if args.hpgsize is None and args.hpgnum is not None:
            msg = "NOTE: hpgnum parameter can not be used alone. Please "\
                  "give value of hpgsize parameter also."
            print msg
            exit(1)

        if args.show_limits:
            self.showlimits(True)
            exit(1)

        self.remove_flavor = args.remove_flavor

        self.showlimits(False)
        if (self.Max2MB < self.default2MB):
            nfv_logger.error(
                "Hugepages can not be enabled if maximum number"
                "of hugepages is less than default number of hugepages.")
            exit(1)

        if args.hpgsize:
            try:
                self.hpgsize = self.calculate_size(args.hpgsize)
            except BaseException:
                msg = args.hpgsize + " :Not a valid value of hpgsize. " \
                    "Valid value is 2MB or 1GB."
                print msg
                exit(1)

        if args.hpgnum is None and args.hpgsize is None:
            self.hpgsize = self.calculate_size("2MB")
            self.hpgnum = self.default2MB
            if self.hpgnum <= self.Max2MB and self.hpgnum >= self.default2MB:
                pass
            else:
                self.showlimits(True)
                print "\033[91m\n\n\nERROR:\033[0m"
                print ("\033[91mDefault Value of Hpgnum: " +
                       str(self.hpgnum) +
                       " is out of range. Range of 'hpgnum' is between " +
                       str(self.default2MB) +
                       " and " +
                       str(self.Max2MB) +
                       ". View the Configuration Limits table above.   \033[0m")
                exit(1)
        elif args.hpgsize != "2MB" and args.hpgsize != "1GB":
            msg = args.hpgsize + " :Not a valid value of hpgsize. " \
                "Valid value is 2MB or 1GB."
            print msg
            nfv_logger.error(args.hpgsize + ':Not a valid value of hpgsize.'
                             'Valid value is 2MB or 1GB.')
            exit(1)

        elif args.hpgnum or args.hpgnum == 0:
            num = int(args.hpgnum)

            if args.hpgsize == "2MB":
                if args.hpgnum <= self.Max2MB and args.hpgnum >= self.default2MB:
                    self.hpgsize = self.calculate_size("2MB")
                    self.hpgnum = args.hpgnum
                else:
                    self.showlimits(True)
                    print "\033[91m\n\n\nERROR:\033[0m"
                    print ("\033[91mValue of hpgnum: " +
                           str(args.hpgnum) +
                           " is out of range. Range of 'hpgnum' is between " +
                           str(self.default2MB) +
                           " and " +
                           str(self.Max2MB) +
                           ". View the Configuration Limits table above.  \033[0m")
                    nfv_logger.error('Value of hpgnum:' + str(args.hpgnum) 
                                     +' is out of range. Range of \'hpgnum\' is between '
                                     + str(self.default2MB) + ' and '
                                     + str(self.Max2MB)+ ' View the Configuration Limits table above.')
                    exit(1)
            elif args.hpgsize == "1GB":
                if args.hpgnum <= self.Max1GB and args.hpgnum >= self.default1GB:
                    self.hpgsize = self.calculate_size("1GB")
                    self.hpgnum = args.hpgnum
                else:
                    self.showlimits(True)
                    print "\033[91m\n\n\nERROR:\033[0m"
                    print ("\033[91mValue of hpgnum: " +
                           str(args.hpgnum) +
                           " is out of range. Range of 'hpgnum' is between " +
                           str(self.default1GB) +
                           " and " +
                           str(self.Max1GB) +
                           ". View the Configuration Limits table above.   \033[0m")
                    exit(1)
            else:
                msg = str(args.hpgnum) + " :Not a valid value of hpgnum. " \
                    "Valid values are 49152 for hpgsize 2MB" \
                    " and 96 for hpgsize 1GB."
                print msg
                exit(1)
        elif args.hpgnum is None and args.hpgsize:
            if args.hpgsize == "2MB":
                self.hpgsize = self.calculate_size("2MB")
                self.hpgnum = self.default2MB
                if self.hpgnum <= self.Max2MB and self.hpgnum >= self.default2MB:
                    pass
                else:
                    self.showlimits(True)
                    print "\033[91m\n\n\nERROR:\033[0m"
                    print ("\033[91mDefault Value of Hpgnum: " 
                    + str(self.hpgnum) + " is out of range. Range of 'hpgnum' is between " 
                    + str(self.default2MB) + " and " + str(self.Max2MB) 
                    + ". View the Configuration Limits table above.   \033[0m")
                    exit(1)
            elif args.hpgsize == "1GB":
                self.hpgsize = self.calculate_size("1GB")
                self.hpgnum = self.default1GB
                if self.hpgnum <= self.Max1GB and self.hpgnum >= self.default1GB:
                    pass
                else:
                    self.showlimits(True)
                    print "\033[91m\n\n\nERROR:\033[0m"
                    print ("\033[91mDefault Value of Hpgnum: " + str(self.hpgnum) 
                    + " is out of range. Range of 'hpgnum' is between " + str(self.default1GB) 
                    + " and " + str(self.Max1GB) 
                    + ". View the Configuration Limits table above.   \033[0m")
                    exit(1)
        self.flavor_metadata = {'hw:mem_page_size': self.hpgsize}

        if args.hostos_memcap:
            if args.hostos_memcap != "8GB":
                msg = args.hostos_memcap + \
                    " :Not a valid value of hostos_memcap." \
                    " Valid value is 8GB."
                print msg
                exit(1)

            self.hostos_memcap = self.calculate_size(args.hostos_memcap)

        if args.action:
            self.action = args.action
            if args.action == "remove" and self.remove_flavor:
                print ("WARNING: All the Hugepages configurations set for " +
                       self.getFlavorName() + " flavor would be wiped out.")
                input = raw_input('Do you still want to continue (y/n): ')
                if input.lower() == "y":
                    pass
                else:
                    print "Exiting the script."
                    sys.exit(1)

        if args.action:
            self.action = args.action
            if self.remove_flavor and self.action == "set":
                print "Flag --remove_flavor is not allowed when " \
                      "--action=set"
                sys.exit(1)

            elif args.action == "remove" and self.remove_flavor is False:
                print ("WARNING: All the Hugepages configurations set for " +
                       self.getFlavorName() + " flavor would be wiped out.")
                input = raw_input('Do you still want to continue (y/n): ')
                if input.lower() == "y":
                    pass
                else:
                    print "Exiting the script."
                    sys.exit(1)

        if args.scope:
            self.scope = args.scope


class RevertChanges:

    def apply_revert(self, arguments):
        update_grub_params = "default_hugepagesz=" + str(arguments.getHpgSize(
                             )) + "K hugepagesz=" + str(arguments.getHpgSize()) + "K hugepages=" +\
                            str(arguments.getHpgNum())
        nfv_logger.info("Starting revert back routine.")

        if arguments.getAction() == 'remove':
            glob.reset_metadata = True
            glob.grub_routine = True
            if arguments.getRemoveFlavor():
                glob.flavor_delete = True
            else:
                glob.flavor_delete = False

        if glob.flavor_delete is True:
            flavorcontrol = FlavorControl(glob)
            try:
                nova = nvclient.Client(
                    2,
                    glob.OverCloud_USERNAME,
                    glob.OverCloud_PASSWORD,
                    glob.OverCloud_PROJECT_ID,
                    glob.OverCloud_AUTH_URL)
            except BaseException:
                nfv_logger.error("Unable to authenticate Nova Client.")
                exit(1)
            flavor_remove_status=flavorcontrol.remove_flavor(nova, arguments.getFlavorName())
            if flavor_remove_status is False:
                nfv_logger.error("Flavor cannot be removed")
                exit(1)
        if glob.flavor_delete is False and glob.reset_metadata is True:
            flavorcontrol = FlavorControl(glob)
            try:
                nova = nvclient.Client(
                    2,
                    glob.OverCloud_USERNAME,
                    glob.OverCloud_PASSWORD,
                    glob.OverCloud_PROJECT_ID,
                    glob.OverCloud_AUTH_URL)
            except BaseException:
                nfv_logger.error("Unable to authenticate Nova Client.")
                exit(1)
            flavorcontrol.remove_flavor_metadata(nova,
                                                 arguments.getFlavorName())

        if glob.grub_routine is True:
            nfv_logger.info("Revert - Removing grub parameters"
                            " on all compute nodes.")

            for i in glob.nodes['compute'].keys():
                ssh_c = glob.nodes['compute'][i]['object'].ssh_connect()
                if ssh_c is True:
                    nfv_logger.info("Removing grub configurations from "
                                    + glob.nodes['compute'][i]['name'])
                    nfv_logger.debug("Removing grub configurations from " 
                                    + glob.nodes['compute'][i]['ip'])
                    update_grub_params = "default_hugepagesz"
                    ssh_stderr, ssh_stdout = \
                        glob.nodes['compute'][i]['object'].execute_command(
                        'grep ' '"HugePages_Total"' ' /proc/meminfo')
                    glob.hugepages_on_node = int(ssh_stdout[0].split()[1])
                    grub_huge_param = None
                    hugepages_num = None
                    if glob.nodes['compute'][i]['object'].validate_grub_params(
                            update_grub_params):
                        nfv_logger.info("Revert - Updating grub of " +
                                        glob.nodes['compute'][i]['name'])
                        nfv_logger.debug("Revert - Updating grub of " +
                                        glob.nodes['compute'][i]['ip'])
                        try:
                            path = '/boot/grub2/grub.cfg'
                            ssh_stdin, ssh_stdout, ssh_stderr = \
                                glob.nodes['compute'][i]['object'].ssh_connection.exec_command(
                                'sudo cat ' + path)
                            remote_file = ssh_stdout.readlines()
                            for line in remote_file:
                                if 'default_hugepagesz' in line:
                                    grub_huge_param = \
                                        line.split('default_hugepagesz')[
                                            1].strip(
                                            "hugepagesz=").split()[0]
                                    hugepages_num = \
                                        line.split('default_hugepagesz')[
                                            1].split()[-1].split(
                                            "=")[-1]
                        except BaseException:
                            nfv_logger.info("Cannot open grub file.")
                        if grub_huge_param is not None and \
                                hugepages_num is not None:
                            nfv_logger.info("Revert - Disabling hugepages on "
                                            + glob.nodes['compute'][i]['name'])
                            nfv_logger.debug("Revert - Disabling hugepages on "
                                            + glob.nodes['compute'][i]['ip'])
                            grub_cmd_line =\
                            glob.nodes['compute'][i]['object'].get_grub_params_line()
                            grub_cmd_line = grub_cmd_line.rstrip()
                            if not grub_cmd_line:
                                nfv_logger.error("Revert - Grub CMD Line parameters not found.")
                                exit(1)

                            if 'default_hugepagesz=' in grub_cmd_line:
                                grub_cmd_line = remove_key_value_pair(
                                    grub_cmd_line, 'default_hugepagesz')

                            if 'hugepagesz=' in grub_cmd_line:
                                grub_cmd_line = remove_key_value_pair(
                                    grub_cmd_line, 'hugepagesz')

                            if 'hugepages=' in grub_cmd_line:
                                grub_cmd_line = remove_key_value_pair(
                                    grub_cmd_line, 'hugepages')

                            grub_cmd_line = re.sub(' +', ' ', grub_cmd_line)
                            glob.disable_update_grub = '/usr/bin/sed ' + "'" + '/GRUB_CMDLINE_LINUX/c' \
                                                  + grub_cmd_line + "'" + \
                                                  ' -i /etc/default/grub'
                            ssh_stderr, ssh_stdout = glob.nodes['compute'][i]['object'].execute_command(
                                                     glob.disable_update_grub)

                            if (len(ssh_stderr) > 0):
                                nfv_logger.error(
                                    "Revert - Error while executing command.")
                            glob.nodes['compute'][i]['object'].execute_command(
                                "/usr/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg")

                        if (glob.hugepages_on_node > 0):
                            time.sleep(10)
                            nfv_logger.info("Hugepages exists. Revert - "
                                            "Rebooting " + glob.nodes['compute'][i]['name'])
                            nfv_logger.debug("Hugepages exists. Revert - "
                                            "Rebooting " + glob.nodes['compute'][i]['ip'])
                            glob.nodes['compute'][i]['object'].execute_command(
                                            "/sbin/shutdown" " -r now")
                            glob.Reboot_Flag = True
                            glob.nodes['compute'][i]['object'].close_ssh_connection()
                        elif glob.hugepages_on_node == 0:
                            nfv_logger.info("Revert - Hugepages do NOT exist"
                                            " on " + glob.nodes['compute'][i]['name'] + ", no need to reboot.")
                            nfv_logger.debug("Revert - Hugepages do NOT exist"
                                            " on " + glob.nodes['compute'][i]['ip'] + ", no need to reboot.")
                    else:
                        nfv_logger.info("Grub parameter does NOT exist on " +
                                        glob.nodes['compute'][i]['ip'] +
                                        ". No need to remove grub parameters. "
                                        "Skipping.")
                        if (glob.hugepages_on_node > 0):
                            time.sleep(10)
                            nfv_logger.info("Revert - Rebooting " + glob.nodes['compute'][i]['name'] +
                                            " to clear last hugepages from the kernel.")
                            nfv_logger.debug("Revert - Rebooting " + glob.nodes['compute'][i]['ip'] +
                                            " to clear last hugepages from the kernel.")
                            glob.nodes['compute'][i]['object'].execute_command(
                                "/sbin/shutdown -r now")
                            glob.Reboot_Flag = True
                            glob.nodes['compute'][i]['object'].close_ssh_connection()
                else:
                    nfv_logger.warning(glob.nodes['compute'][i]['name'] 
                                      + glob.nodes['compute'][i]['ip']
                                      + " is not available,"
                                       " unable to revert grub parameters.")
            
            #shutdown routine should be called here
            time.sleep(10)
            i = 0
            sec_counter = 0
            if glob.Reboot_Flag is True:
                nfv_logger.info("Waiting for the nodes to be rebooted.")
                time.sleep(30)
            timer = 360 + 40 * \
                (int(math.ceil((len(glob.nodes['compute'].keys()) - 3) / float(3))))
            timer_check = 0
            for i in glob.nodes['compute'].keys():
                timer_check = timer_check + \
                    int(os.system('ping -c 1 -W 5 ' + glob.nodes['compute'][i]['ip'] + '>/dev/null 2>&1'))
            if timer_check == 0:
                nfv_logger.info("All nodes are up, skipping timer.")
            UpNodes = []
            if timer_check > 0:
                nfv_logger.info("Revert - Timer expiry is set to " + str(
                    timer) + " seconds.")
                for i in glob.nodes['compute'].keys():
                    ping_cmd = 'ping -c 1 -W 1 ' + \
                        glob.nodes['compute'][i]['ip'] + '>/dev/null 2>&1'
                    while os.system(ping_cmd) != 0:
                        nfv_logger.info('Waiting for ' + glob.nodes['compute'][i]['name'])
                        nfv_logger.debug('Waiting for '+ glob.nodes['compute'][i]['ip'])
                        time.sleep(10)
                        sec_counter = sec_counter + 10
                        if sec_counter >= timer:
                            nfv_logger.info("Timer is expired, waited for " +
                                            str(sec_counter) + " seconds at "
                                            "Compute-" + str(i) + " " +
                                            glob.nodes['compute'][i]['ip'])
                            break
                    if sec_counter < timer:
                        nfv_logger.info(glob.nodes['compute'][i]['name'] + ' is up')
                        nfv_logger.debug(glob.nodes['compute'][i]['ip'] + ' is up')
                        i += 1
                    elif sec_counter >= timer:
                        break

            for j in glob.nodes['compute'].keys():
                ping_cmd = 'ping -c 1 -W 1 ' + \
                    glob.nodes['compute'][j]['ip'] + '>/dev/null 2>&1'
                if os.system(ping_cmd) == 0:
                    UpNodes.append('up')
                    if sec_counter >= timer:
                        nfv_logger.info(glob.nodes['compute'][j]['name'] 
                                       +' is up.')
                        nfv_logger.debug(glob.nodes['compute'][j]['ip'] 
                                       +' is up.')

                else:
                    nfv_logger.info(glob.nodes['compute'][j]['name'] 
                                    +' is down.')
                    nfv_logger.debug(glob.nodes['compute'][j]['ip'] 
                                    +' is down.')
                    UpNodes.append('down')

            i = 0
            time.sleep(10)
            nfv_logger.info("Now trying to verify the revert "
                            "process through ssh in each compute node.")
            verify = True
            for i in glob.nodes['compute'].keys():
                for retry in range(glob.SSH_RETRIES):
                    ssh_c = glob.nodes['compute'][i]['object'].ssh_connect()
                    if ssh_c is True:
                        ssh_stderr, ssh_stdout = glob.nodes['compute'][i]['object'].execute_command(
                            'grep "HugePages_Total" /proc/meminfo')
                        glob.hugepages_on_node = int(ssh_stdout[0].split()[1])
                        if glob.hugepages_on_node != 0:
                            nfv_logger.error('Revert - Hugepages verification on ' 
                                            + glob.nodes['compute'][i]['ip'] 
                                            + ' failed.')
                            verify = False
                        else:
                            nfv_logger.info('Revert - Hugepages removal verification on ' 
                                            + glob.nodes['compute'][i]['name'] 
                                            +' passed.')
                            nfv_logger.debug('Revert - Hugepages removal verification on ' 
                                            + glob.nodes['compute'][i]['ip'] 
                                            +' passed.')

                        break
                    else:
                        nfv_logger.warning('TRY_NUMBER: ' + str(retry) 
                                          +' Unable to ssh on '
                                          +glob.nodes['compute'][i]['ip'])
                        nfv_logger.info('Sleeping for 10 seconds.')
                        time.sleep(10)
                if retry >= glob.SSH_RETRIES - 1:
                    nfv_logger.error('Revert - Hugepages verification on'
                                     ' Compute-' + str(i) + " " +
                                     glob.nodes['compute'][i]['ip'] + ' failed.'
                                     ' Unable to ssh')
                    verify = False

            if verify is True:
                nfv_logger.info("Revert - Hugepages configurations have been"
                                " removed from all compute nodes"
                                " successfully.")
            elif verify is False:
                nfv_logger.info("Revert - Hugepages configurations"
                                " on some nodes."
                                " have failed (check logs),"
                                " manual intervention of user is required.")

            exit(0)


def get_nodes(username, password, url):
    
    try:
        headers = {'Content-Type': 'application/json', }
        data = '{"auth":{"passwordCredentials":{"username": "'\
               + str(username) + '","password": "' + str(password)\
               + '"},"tenantName": "admin"}}'
        request_url = os.path.join(url, 'tokens')
        token = requests.post(request_url, data=data, headers=headers)
        token_id = str(token.json()['access']['token']['id'])
        headers = {'X-Auth-Token': token_id, }
        request_url = os.path.join(url, 'tenants')
        tenants = requests.get(request_url, headers=headers)
        for i in tenants.json()['tenants']:
            if i['name'] == 'admin':
                tenant_id = str(i['id'])
                loop_end_flag = 1
                break
        if loop_end_flag == 0:
            nfv_logger.error("Tenant='admin' NOT found. Exiting the "
                             "script.")
            exit(1)
        request_url = os.path.join(url, 'tokens/' + token_id + '/endpoints')
        end_point_list = requests.get(request_url, headers=headers)
        loop_end_flag = 0
        for i in end_point_list.json()['endpoints']:
            if i['name'] == 'nova':
                nova_endpoint = str(i['adminURL'])
                loop_end_flag = 1
                break
        if loop_end_flag == 0:
            nfv_logger.error("Nova_URL NOT found. Exiting the script.")
            exit(1)

        request_url = os.path.join(nova_endpoint + '/servers/detail')
        hosts = requests.get(request_url, headers=headers)

    except requests.exceptions.ConnectTimeout as e:
        nfv_logger.error("Request timed-out, check authentication_url.")
        exit(1)
    except requests.exceptions.ConnectionError as e:
        nfv_logger.error("Invalid authentication_url.")
        exit(1)

    except BaseException:
        nfv_logger.error("Unable to authenticate."
                         " Please check authentication_url,"
                         " openstack_admin_username"
                         " or openstack_admin_password.")
        exit(1)

    if hosts.status_code == 404:
        nfv_logger.error("404, unable to connect to OpenStack Director,"
                         " invalid url.")
        exit(1)

    if isinstance(hosts.json(), dict) and hosts.status_code == 401:
        nfv_logger.error("OpenStack Director"
                         " Error: " + str(hosts.json()['message']))
        exit(1)

    elif hosts.status_code == 200:
        control_list = []
        compute_list = []

        for server in hosts.json()['servers']:
            if 'control' in server['name']:
                control_list.append((server['name'], server['addresses'][
                    'ctlplane'][0]['addr']))
            elif 'compute' in server['name']:
                compute_list.append((server['name'], server['addresses'][
                    'ctlplane'][0]['addr']))

        control_list = sorted(control_list, key=lambda tup: tup[0])
        compute_list = sorted(compute_list, key=lambda tup: tup[0])

        for t in compute_list:
            id = compute_list.index(t)
            # print nodes
            glob.nodes['compute'][id] = {}
            glob.nodes['compute'][id]['name'] = t[0]
            glob.nodes['compute'][id]['ip'] = t[1]
            glob.nodes['compute']

        for t in control_list:
            glob.nodes['control'][control_list.index(t)] = {}
            glob.nodes['control'][control_list.index(t)]['name'] = t[0]
            glob.nodes['control'][control_list.index(t)]['ip'] = t[1]
        # print nodes

    else:
        nfv_logger('Director: status_code ' + str(hosts.status_code))
        exit(1)


def memory_sanity_check(arguments):

    for i in glob.nodes['compute'].keys():
        ssh_c = glob.nodes['compute'][i]['object'].ssh_connect()
        if ssh_c is True:
            memory_check_command_new = "dmidecode -t memory 17 | grep MB"
            ssh_stderr, ssh_stdout = glob.nodes['compute'][i]['object'].execute_command(
                memory_check_command_new)
            host_total_memory = 0
            for line in ssh_stdout:
                output = line.split()[1]
                if output.isdigit():
                    host_total_memory += int(output)
            host_total_memory = host_total_memory * 1024
            hpgsize = arguments.getHpgSize()
            hpgnum = arguments.getHpgNum()
            hostos_memcap = arguments.getHostMemcap() + arguments.host_memcap_extra

            memory_for_hugepages = hpgsize * hpgnum
            memory_sum = memory_for_hugepages + hostos_memcap

            try:
                if memory_sum <= host_total_memory:
                    nfv_logger.info("Memory sanity test "
                                    "successful for " + glob.nodes['compute'][i]['name'])
                    nfv_logger.debug("Memory sanity test "
                                    "successful for " + glob.nodes['compute'][i]['ip'] )
                else:
                    nfv_logger.error("Memory sanity test failed"
                                     " (memory for hugepages and host OS "
                                     "exceeds the available memory) for " +
                                     compute_host_names[i])
                    raise ValueError("Memory sanity test failed"
                                     " (memory for hugepages and"
                                     " host OS exceeds the"
                                     " available memory) for " +
                                     compute_host_names[i])
            except ValueError as err:
                nfv_logger.info(err.args)
                exit(1)
        else:
            nfv_logger.warning('Compute-' + str(i) + ' ' +
                               str(compute_host_names[i]) +
                               ' is not available; '
                               'could not do Memory sanity check.')
            nfv_logger.error('Aborting the operation. Check log for details.')
            exit(1)


def verify_config(arguments):
    #global hugepages_on_node, Reboot_Flag
    timer = 360 + 40 * \
        (int(math.ceil((len(glob.nodes['compute'].keys()) - 3) / float(3))))
    if glob.Reboot_Flag is True:
        nfv_logger.info("Waiting for the nodes to be rebooted.")
        time.sleep(30)
    timer_check = 0
    for i in glob.nodes['compute'].keys():
        timer_check = timer_check + int(os.system('ping -c 1 -W 5 ' +
                                                  glob.nodes['compute'][i]['ip'] +
                                                  '>/dev/null 2>&1'))
    if timer_check == 0:
        nfv_logger.info("All nodes are up, skipping timer.")

    if timer_check > 0:
        nfv_logger.info("Timer expiry is set to " + str(timer) + " seconds.")
        i = 0
        sec_counter = 0
        for i in glob.nodes['compute'].keys():
            ping_cmd = 'ping -c 1 -W 1 ' + \
                glob.nodes['compute'][i]['ip'] + '>/dev/null 2>&1'
            while os.system(ping_cmd) != 0:
                nfv_logger.info('Waiting for ' + glob.nodes['compute'][i]['name'])
                nfv_logger.debug('Waiting for ' + glob.nodes['compute'][i]['ip'])
                time.sleep(10)
                sec_counter = sec_counter + 10
                if sec_counter >= timer:
                    nfv_logger.info("Timer is expired, waited for " +
                                    str(sec_counter) + " seconds.")
                    return False
            nfv_logger.info(glob.nodes['compute'][i]['name'] + ' is up.')
            nfv_logger.debug(glob.nodes['compute'][i]['ip'] + ' is up.')
            i += 1
        nfv_logger.info("Waiting for the ssh daemon to start.")
        time.sleep(25)
        # SSh deamon takes some time to start after ping reply, wait for that
        # TO_DO: In next version, ensure that ssh deamon has started before
        # calling verification function

    i = 0
    status = True
    for i in glob.nodes['compute'].keys():
        ssh_successful = False
        for retry in range(glob.SSH_RETRIES):
            ssh_c = glob.nodes['compute'][i]['object'].ssh_connect()
            if ssh_c is True:
                ssh_successful = True
                ssh_stderr, ssh_stdout = glob.nodes['compute'][i]['object'].execute_command(
                    'grep "HugePages_Total" /proc/meminfo')
                glob.hugepages_on_node = int(ssh_stdout[0].split()[1])
                if glob.hugepages_on_node != arguments.getHpgNum():
                    nfv_logger.error('Hugepages verification on ' 
                                    + glob.nodes['compute'][i]['ip']
                                    +' failed.')
                    status = False
                else:
                    nfv_logger.info('Hugepages verification on '
                                    + glob.nodes['compute'][i]['name']
                                    +' passed.')
                    nfv_logger.debug('Hugepages verification on '
                                    + glob.nodes['compute'][i]['ip'] 
                                    +' passed.')

                break
            else:
                nfv_logger.warning('TRY_NUMBER: ' + str(retry) +
                                  ' Unable to ssh on ' 
                                  + glob.nodes['compute'][i]['name'] + ' ' 
                                  + glob.nodes['compute'][i]['ip'])
                nfv_logger.info('Sleeping for 10 seconds.')
                time.sleep(10)

            if not ssh_successful:
                nfv_logger.warning(glob.nodes['compute'][i]['name'] +
                                   ' is not available. Could Not verify'
                                   ' the set configurations.')
                status = False

        if status is True:
            nfv_logger.info('Hugepages verification on ' 
                            + glob.nodes['compute'][i]['name'] 
                            +' has been done successfully.')
            nfv_logger.debug('Hugepages verification on ' 
                            + glob.nodes['compute'][i]['ip'] 
                            +' has been done successfully.')

    return status


'''
This are to for WhiteListing the logs
'''


class Whitelist(Logger.Filter):
    def __init__(self, *whitelist):
        self.whitelist = [Logger.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)


'''
This are to for BlackListing the logs
'''


class Blacklist(Whitelist):
    def filter(self, record):
        return not Whitelist.filter(self, record)


def getOvercloudrcFileName(username, password, url):

    try:
        headers = {'Content-Type': 'application/json', }
        data = '{"auth":{"passwordCredentials":{"username": "' + str(
            username) + '","password": "' + str(
            password) + '"},"tenantName": "admin"}}'
        request_url = os.path.join(url, 'tokens')
        token = requests.post(request_url, data=data, headers=headers)
        token_id = str(token.json()['access']['token']['id'])
        headers = {'X-Auth-Token': token_id, }
        request_url = os.path.join(url, 'tenants')
        tenants = requests.get(request_url, headers=headers)
        loop_end_flag = 0
        for i in tenants.json()['tenants']:
            if i['name'] == 'admin':
                tenant_id = str(i['id'])
                loop_end_flag = 1
                break
        if loop_end_flag == 0:
            nfv_logger.error("Tenant='admin' NOT found. Exiting the "
                             "script.")
            exit(1)
        request_url = os.path.join(url, 'tokens/' + token_id + '/endpoints')
        end_point_list = requests.get(request_url, headers=headers)
        loop_end_flag = 0
        for i in end_point_list.json()['endpoints']:
            if i['name'] == 'heat':
                heat_endpoint = str(i['adminURL'])
                loop_end_flag = 1
                break
        if loop_end_flag == 0:
            nfv_logger.error("Heat endpoint NOT found for overcloud."
                             " Exiting the script.")
            exit(1)

        request_url = os.path.join(heat_endpoint + '/stacks')
        stacks = requests.get(request_url, headers=headers)
        try:
            first_stack_name = str(stacks.json()['stacks'][0]['stack_name'])
        except BaseException:
            nfv_logger.error("No undercloud stack exits. Exiting the script.")
            exit(1)
    except requests.exceptions.ConnectTimeout as e:
        nfv_logger.error("Request timed-out, check authentication_url.")
        exit(1)
    except requests.exceptions.ConnectionError as e:
        nfv_logger.error("Invalid authentication_url.")
        exit(1)

    except BaseException:
        nfv_logger.error(
            "Unable to authenticate. Please check authentication_url,"
            " openstack_admin_username or openstack_admin_password.")
        exit(1)

    stack_name = first_stack_name + 'rc'
    return stack_name


def authenticate_undercloud(director_install_user):

    if glob.UnderCloud_USERNAME == '' or glob.UnderCloud_PASSWORD == '' or glob.UnderCloud_PROJECT_ID == ''\
            or glob.UnderCloud_AUTH_URL == '':
        file_path = '/home/' + director_install_user + '/' + \
                    'stackrc'
        if not os.path.isfile(file_path):
            nfv_logger.error("File '" + file_path + "' does not exits."
                             " Cannot authenticate Nova client.")
            nfv_logger.info('Script execution failed.')
            exit(1)

        try:
            rc_file = open(file_path)
        except BaseException:
            nfv_logger.error(
                "Undercloud file " +
                file_path +
                " cannot be opened ")

        try:

            for line in rc_file:
                if 'OS_USERNAME=' in line:
                    glob.UnderCloud_USERNAME = line.split('OS_USERNAME=')[1].strip(
                        "\n").strip("'")
                elif 'OS_PASSWORD=' in line:
                    cmd = 'sudo hiera admin_password'
                    proc = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
                    output = proc.communicate()
                    output = output[0]
                    glob.UnderCloud_PASSWORD = output[:-1]
                elif 'OS_TENANT_NAME=' in line:
                    glob.UnderCloud_PROJECT_ID = line.split('OS_TENANT_NAME=')[
                        1].strip("\n").strip("'")
                elif 'OS_AUTH_URL=' in line:
                    glob.UnderCloud_AUTH_URL = line.split('OS_AUTH_URL=')[1].strip(
                        "\n").strip("'")

            nova = nvclient.Client(2, glob.UnderCloud_USERNAME, glob.UnderCloud_PASSWORD,
                                   glob.UnderCloud_PROJECT_ID, glob.UnderCloud_AUTH_URL)

            return nova
        except BaseException:
            nfv_logger.error("Authenticating Undercloud failed.")
            exit(1)
    else:
        try:
            nova = nvclient.Client(2, glob.UnderCloud_USERNAME, glob.UnderCloud_PASSWORD,
                                   glob.UnderCloud_PROJECT_ID, glob.UnderCloud_AUTH_URL)
            return nova
        except BaseException:
            nfv_logger.error("Authenticating Undercloud failed.")
            exit(1)


def authenticate_check(args):

    for i in glob.nodes['compute'].keys():
        computeconfig = ComputeConfig(i, glob.nodes['compute'][i]['ip'],
                                      glob.nodes['compute'][i]['name'],glob)
        glob.nodes['compute'][i]['object'] = computeconfig
        ssh_c = computeconfig.ssh_connect()
        ssh_c = glob.nodes['compute'][i]['object'].ssh_connect()
        if ssh_c is False:
            nfv_logger.warning('Unable to ssh in Compute-' + str(i) +
                               ' ' + compute_host_names[i])
            nfv_logger.error('Aborting the operation. Check log for details.')
            exit(1)

    overcloudrc_file_name = getOvercloudrcFileName(
        args.getUndercloudUsername(), args.getUndercloudPassword(),
        args.getAuthenticationUrl())
    authenticate_overcloud(args.getDirectorInstallUser(),
                           overcloudrc_file_name)


def Compute_Config_Test(args):
    nfv_logger.info("Verifying configurations on all compute nodes")
    for i in glob.nodes['compute'].keys():
        ssh_c = glob.nodes['compute'][i]['object'].ssh_connect()
        if ssh_c is True:
            ssh_stderr, ssh_stdout = glob.nodes['compute'][i]['object'].execute_command(
                'grep ' '"HugePages_Total"' ' /proc/meminfo')
            #hugepages_on_node = int(ssh_stdout[0].split()[1])
            glob.hugepages_on_node = int(ssh_stdout[0].split()[1])
            if glob.hugepages_on_node is not None and glob.hugepages_on_node == 0:
                pass
            elif glob.hugepages_on_node > 0:
                nfv_logger.info(" Hugepages already exists on " +
                                glob.nodes['compute'][i]['ip'] +
                                "\nNOTE: If you want "
                                "to change the hugepage size,"
                                " please first run the 'enable_hugepages.py'"
                                " script with parameter --action=remove,"
                                " and then re-run the command"
                                " with --action= set")
                exit(1)
        else:
            nfv_logger.warning('Compute-' + str(i) + ' is unavailable for ssh,'
                               ' could not check for set configurations.')
    return True


def authenticate_overcloud(director_install_user, overcloudrc_file_name):

    nfv_logger.info("Authenticating Nova client.")
    #global OverCloud_USERNAME, glob.OverCloud_PASSWORD, glob.OverCloud_PROJECT_ID, OverCloud_AUTH_URL
    if glob.OverCloud_USERNAME == '' or glob.OverCloud_PASSWORD == '' or glob.OverCloud_PROJECT_ID == ''\
            or glob.OverCloud_AUTH_URL == '':
        file_path = '/home/' + director_install_user + '/' + \
                    overcloudrc_file_name
        if not os.path.isfile(file_path):
            nfv_logger.error(
                "File '" + file_path + "' does not exits."
                " Cannot authenticate Nova client.")
            nfv_logger.info('Exiting the script.')
            exit(1)

        try:
            rc_file = open(file_path)
        except BaseException:
            nfv_logger.error(
                "Cannot open '" + file_path + "'")

        try:
            for line in rc_file:
                if 'OS_USERNAME' in line:
                    glob.OverCloud_USERNAME = line.split('OS_USERNAME=')[1].strip(
                        "\n").strip("'")
                elif 'OS_PASSWORD' in line:
                    glob.OverCloud_PASSWORD = line.split('OS_PASSWORD=')[1].strip(
                        "\n").strip("'")
                elif 'OS_PROJECT_NAME' in line:
                    glob.OverCloud_PROJECT_ID = line.split('OS_PROJECT_NAME=')[
                        1].strip("\n").strip("'")
                elif 'OS_AUTH_URL' in line:
                    glob.OverCloud_AUTH_URL = line.split('OS_AUTH_URL=')[1].strip(
                        "\n").strip("'")

            nova = nvclient.Client(2, glob.OverCloud_USERNAME, glob.OverCloud_PASSWORD,
                                   glob.OverCloud_PROJECT_ID, glob.OverCloud_AUTH_URL)

            nfv_logger.info("Authenticating Nova client successful.")

            return nova
        except BaseException:
            nfv_logger.error(
                "Authenticating Nova client failed.")
            exit(1)
    else:
        try:
            nova = nvclient.Client(2, glob.OverCloud_USERNAME, glob.OverCloud_PASSWORD,
                                   glob.OverCloud_PROJECT_ID, glob.OverCloud_AUTH_URL)
            return nova
        except BaseException:
            nfv_logger.error(
                "Authenticating Nova client failed.")
            exit(1)

# Input is a string, and a key. Matches the key value pair and remove it
# from the string.


def remove_key_value_pair(input_string, key):
    return re.sub(key + '=[^\s"]+', '', input_string)


if __name__ == "__main__":

    
    '''
    Reading the command line arguments
    using the 'ArgumentParser' class
    '''
    glob = GlobVar()  # Global variables class
    
    args = ArgumentParser(glob)
    args.read_args_hugepages(sys.argv)

    if pwd.getpwuid(os.getuid())[0] != args.getDirectorInstallUser():
        print "Please login as user '" + args.getDirectorInstallUser() + \
              "' and then re-run the script."\
            " Or provide different Director username for" \
              " director_install_user input parameter."
        exit(1)

    print '\033[38;5;2m__          __     _____  _   _ _____ _   _  _____ '
    print '\ \        / /\   |  __ \| \ | |_   _| \ | |/ ____|'
    print ' \ \  /\  / /  \  | |__) |  \| | | | |  \| | |  __ '
    print '  \ \/  \/ / /\ \ |  _  /| . ` | | | | . ` | | |_ |'
    print '   \  /\  / ____ \| | \ \| |\  |_| |_| |\  | |__| |'
    print '    \/  \/_/    \_\_|  \_\_| \_|_____|_| \_|\_____|\033[0m'
    print ("\nThis script may reboot all compute nodes "
           "in the solution multiple times.\n"
           "Already running INSTANCES might not work after the "
           "script execution. \n"
           "Please save your work, stop pertinent services, "
           "and ask users to completely log out before proceeding. \nDo not "
           "reboot the nodes manually while the script is running.")
    input = raw_input('Do you still want to continue (y/n): ')

    if input.lower() == "y":
        pass
    else:
        print "Exiting the script."
        sys.exit(1)

    for handler in Logger.root.handlers:
        handler.addFilter(Blacklist('dell_nfv_logger'))

    '''
    Getting the IPs of
    compute nodes from director.
    '''
    get_nodes(args.getUndercloudUsername(), args.getUndercloudPassword(),
              args.getAuthenticationUrl())
    nfv_logger.info("Received Compute Node List from OpenStack Director:")

    '''
    Logging in compute in nodes and authenticating nova client.
    '''

    authenticate_check(args)

    '''
    Performing tests to check if the
    memory for hugepages and host OS
    doesn't exceeds the available
    memory on each Compute Node
    '''

    memory_sanity_check(args)

    '''
    Checking if the hugepages are already
    enabled in any one of the nodes or not
    improvement required here in script execution failed'''
    verified = ""
    if args.action == "set":
        config_test = Compute_Config_Test(args)
        if not config_test:
            print "Script execution failed. Please check log for details."
            sys.exit(1)
        else:
            nfv_logger.info("No hugepages configurations exists."
                            " Continuing configurations.")

        '''
        Applying Flavor configurations
        '''
        # ControlConfig.apply_config(args)
        flavorcontrol=FlavorControl(glob)
        flavorcontrol.apply_config(args)
        '''
        Looping through the compute nodes here.
        In each iteration, calling ssh and apply
        config on each node
        '''
        for i in glob.nodes['compute'].keys():
            ssh_c = glob.nodes['compute'][i]['object'].ssh_connect()
            if ssh_c is True:
                glob.nodes['compute'][i]['object'].apply_config(args)

            else:
                nfv_logger.warning('Compute-' + str(i) +
                                   ' is not available. Calling revert routine'
                                   ' after verification.')
                verify_config(args)
                revert_changes = RevertChanges()
                revert_changes.apply_revert(args)
                exit(1)

        verified = verify_config(args)

    elif args.getAction() == 'remove':
        nfv_logger.info('As action=remove, reverting all changes.')
        revert_changes = RevertChanges()
        revert_changes.apply_revert(args)

    if verified is True:
        nfv_logger.info("Hugepages configuration test passed.")
        if args.getLogFile() != 'stdout':
            print "If you used the --logfile option on the command line, please check log file \'%s\' for a copy of this on-screen ouput." % (args.logfile)

        else:
            print "Script executed successfully."
    if verified is False:
        nfv_logger.error("Hugepages configurations test failed;"
                         " calling revert routine.")
        revert_changes = RevertChanges()
        revert_changes.apply_revert(args)
        exit(1)
