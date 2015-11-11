#------------python lib imports-----------#
import os
import time
import select
import sys
from collections import namedtuple
import readline
import paramiko
import json
import logging
import datetime
import time
#==========================================#
#-------------functions import-------------#
from os_defs import *
from consts import *
from file_defs import *
#==========================================#

# ======================= PROMPT INPUT AND CREDENTIALS FUNCTIONS =====================#
def count_down(time_sleep):
	for i in range(0, time_sleep):
		sys.stdout.write('Starting deployment in ' + str(time_sleep-i) + '... \r')
		sys.stdout.flush()
		time.sleep(1)
def check_input(predicate, msg, error_string = "Invalid Input"):
	while True:
		result = raw_input(msg)
		if predicate(result):
			return result
		print(error_string)
# Prompt user to input value or use default value
def take_input(prompt, def_val):
	inp = raw_input(prompt + ' <default: ' + def_val + '>: ')
	if(inp == ''):
		return def_val
	else:
		return inp
#==================================================================================#