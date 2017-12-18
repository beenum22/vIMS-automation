#For the unit testing
#
import unittest
from mock import patch, MagicMock
import units
import string
import openpyxl
from hpsrc.ComputeConfig import ComputeConfig
#from hpsrc.FlavorControl import FlavorControl
from hpsrc.GlobVar import GlobVar
import paramiko
#import novaclient
#from novaclient import client
#from novaclient import client as nvclient
#import enable_hugepages_director
import requests
import json


class TestInputArgument(unittest.TestCase):
    
    def setUp(self):
        self.wb = openpyxl.load_workbook('hugepages_unittesting/test_cases.xlsx')
        
    def test_positive_logfile_name(self):
        positive_sheet = self.wb.get_sheet_by_name('positive')
        num_entries=2 #starting cell in excell sheet
        #print(len(positive_sheet['G']))
        #len(positive_sheet['A'])-1 <-- minus 1 is because of avoiding none 
        #print('C')
        #print(len(positive_sheet['C']))
        while((num_entries) <= (len(positive_sheet['G'])-1) ):
            value='G'+str(num_entries)
            #print(value)
            #print(positive_sheet[value].value)
            status = units.logfile_name(positive_sheet[value].value)
            #print(status)
            self.assertTrue(status)
            #print('passed')
            num_entries=num_entries+1
    
    def test_negative_logfile_name(self):
        negative_sheet = self.wb.get_sheet_by_name('negative')
        num_entries=2 #starting cell in excell sheet
        #print(len(negative_sheet['G']))
        #len(positive_sheet['A'])-1 <-- minus 1 is because of avoiding none 
        while((num_entries) <= (len(negative_sheet['G'])-1) ):
            value='G'+str(num_entries)
            #print(value)
            #print(negative_sheet[value].value)
            status = units.logfile_name(negative_sheet[value].value)
            #print(status)
            self.assertFalse(status)
            #print('passed')
            num_entries=num_entries+1
    
    def test_positive_flavor_name(self):
        positive_sheet = self.wb.get_sheet_by_name('positive')
        num_entries=2 #starting cell in excell sheet
        #print(len(positive_sheet['A']))
        #len(positive_sheet['A'])-1 <-- minus 1 is because of avoiding none 
        while((num_entries) <= (len(positive_sheet['A'])-1) ):
            value='A'+str(num_entries)
            #print(value)
            #print(positive_sheet[value].value)
            status = units.logfile_name(positive_sheet[value].value)
            #print(status)
            self.assertTrue(status)
            #print('passed')
            num_entries +=num_entries
    
    def test_negative_flavor_name(self):
        negative_sheet = self.wb.get_sheet_by_name('negative')
        num_entries=2 #starting cell in excell sheet
        #print(len(negative_sheet['A']))
        #len(positive_sheet['A'])-1 <-- minus 1 is because of avoiding none 
        while((num_entries) <= (len(negative_sheet['A'])-1) ):
            value='A'+str(num_entries)
            #print(value)
            #print(negative_sheet[value].value)
            status = units.logfile_name(negative_sheet[value].value)
            #print(status)
            self.assertFalse(status)
            #print('passed')
            num_entries +=num_entries
            
class TestComputeConfig(unittest.TestCase):
    
    def setUp(self):
        self.glob=GlobVar()
        self.cc=ComputeConfig('osp_admin', '127.0.0.1' , 'test', self.glob)
        ssh_conn = paramiko.SSHClient()
        ssh_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_connection = ssh_conn
    
    def test_positive_ssh(self):
        status = self.cc.ssh_connect()
        self.assertTrue(status)
        
    def test_negative_ssh(self):
        status = self.cc.ssh_connect()
        self.assertFalse(status)
'''    
    def test_positive_execute_command(self):
        pass
        #Traceback (most recent call last):
        #File "test.py", line 106, in test_positive_execute_command
        #status =self.ssh_connection.exec_command(command)
        #File "/usr/lib/python2.7/site-packages/paramiko/client.py", line 435, in exec_command
        #chan = self._transport.open_session(timeout=timeout)
        #AttributeError: 'NoneType' object has no attribute 'open_session'

        #command='ls'
        #status =self.ssh_connection.exec_command(command)
        #print(status)
        #self.assertEqual(status, True)
    
    def test_negative_execute_command(self):
        #with patch('cc.ssh_connect') as mock_execute_command:
        #    mock_execute_command.return_value = True
        pass
    def test_positive_validate_grub_params(self):
        pass
    def test_positive_get_grub_params_line(self):
        pass
        
class TestFlavorControl(unittest.TestCase):
    
    def setUp(self):
        self.nova = nvclient.Client(
            2,
            'admin',
            'YexCfh82n4KXukbmdUEcxTh6g',
            'admin',
            'http://192.0.2.13:5000/v2.0')
        self.glob=GlobVar()
        self.cc=FlavorControl(self.glob)
        self.wb = openpyxl.load_workbook('test_cases.xlsx')
    def test_positive_create_flavor(self):
        status = self.cc.create_flavor(self.nova,'test')
        self.assertEqual(str(status), '<Flavor: test>')
    
    def test_negative_create_flavor(self):
        status = self.cc.create_flavor(self.nova,'test')
        self.assertEqual(str(status), '<Flavor: test>')
        negative_sheet = self.wb.get_sheet_by_name('negative')
        if units.flavor_name(negative_sheet['A2'].value) is False:
            status_remove_flavor = False
        self.assertFalse(status_remove_flavor)
        
    def test_positive_remove_flavor(self):
        status=self.cc.remove_flavor(self.nova,'test')
        self.assertTrue(status)
    
    def test_negative_remove_flavor(self):
        #status=self.cc.remove_flavor(self.nova,'test')
        #self.assertFalse(status)
        pass
    
    def test_positive_remove_flavor_metadata(self):
        #this test needs to be corrected further
        flavor=self.cc.create_flavor(self.nova,'test')
        self.cc.remove_flavor(self.nova,'test')
        status=self.cc.remove_flavor_metadata(self.nova,str(flavor))
        self.assertTrue(status)
        
        
    def test_positive_set_flavor_metadata(self):
        pass
        #flavor=self.cc.create_flavor(self.nova,'test')
        #flavor_metadata[0]=2048
        #status=self.cc.set_flavor_metadata(flavor,flavor_metadata)
        #self.assertTrue(status)
    

class OverCloudFilename(unittest.TestCase):
    def setUp(self):
        self.username='admin'
        self.password='YexCfh82n4KXukbmdUEcxTh6g'
        self.url='http://192.0.2.13:5000/v2.0'
    def test_getOvercloudFileName(self):
        status=getOvercloudrcFileName(self.username,self.password,self.url)
        self.assretEqual(status,'overcloudrc')
'''        
        
if __name__=='__main__':
    unittest.main()
