import subprocess
from urllib2 import urlopen, URLError, HTTPError
import string
import random
import logging
import socket
import os
import re
import ipaddress
#from ssh import SSHConnection
#from ssh import *
#import paramiko

logger = logging.getLogger(__name__)


class Utilities(object):

    def __init__(self):
        pass

    @staticmethod
    def _cmd_async(cmd, pipe_in=None, pipe_out=False, shell=False):  # Exception not correct yet
        '''To store output and error if needed'''
        try:
            p = subprocess.Popen(
                cmd,
                shell=shell,
                stdin=pipe_in,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            if pipe_out:
                return p, None
            output, err = p.communicate()
            return output, err
        except subprocess.CalledProcessError as err:
            logger.debug(err)
            raise
        except OSError as err:
            logger.debug(err)
            logger.error("Invalid command '%s'.", cmd)
            raise Exception("'%s' command execution failed" % cmd)

    @staticmethod
    def _cmd_sync(*cmd, **kwargs):
        try:
            # print kwargs.get('pipe_in')
            if kwargs.get('pipe_in'):
                # print kwargs['pipe_in']
                # if 'pipe_in' in kwargs:
                output = subprocess.check_output(
                    cmd, stdin=kwargs['pipe_in'].stdout)
            else:
                output = subprocess.check_output(cmd)
            return output
        except subprocess.CalledProcessError as err:
            logger.debug(err)
            raise
        except OSError:
            logger.error("Invalid command '%s'.", cmd)
            raise

    @staticmethod
    def _bash_script(script, *args):
        '''This function is used for bash scripts as we want to see the output'''
        '''and for that we used check_call function from subprocess'''
        cmd = []
        cmd.append(script)
        for a in args:
            cmd.append(a)
        try:
            output = subprocess.check_call(cmd)
            return output
        except subprocess.CalledProcessError as err:
            logger.debug(err)
            logger.error("Failed to execute '%s'.", cmd)
            raise
        except KeyboardInterrupt:
            logger.error("Execution aborted...")
            raise

    @staticmethod
    def _create_dir(directory):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except OSError:
            logger.error("Failed to create the '%s' directory", directory)
            raise

    @staticmethod
    def _random_str(size=15, chars=None):
        if not chars:
            chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    @staticmethod
    def _strip_list_items(l):
        return [x.strip() for x in l]

    @staticmethod
    def _str_to_tuple(s, delimiter=None):
        return tuple(filter(None, s.split(delimiter)))

    @classmethod
    def run_cmd(cls, cmd):
        try:
            if '|' in cmd:
                cmd = cls._strip_list_items(cmd.split('|'))
                output = None
                pipe = True
                for i in range(0, len(cmd)):
                    if i == len(cmd) - 1:
                        pipe = False
                    if output:
                        output, err = cls._cmd_async(cls._str_to_tuple(
                            cmd[i]), pipe_in=output.stdout, pipe_out=pipe)
                    else:
                        output, err = cls._cmd_async(
                            cls._str_to_tuple(cmd[i]), pipe_out=pipe)
                return output.strip(), err.strip()
            else:
                output, err = cls._cmd_async(cls._str_to_tuple(cmd))
                return output.strip(), err.strip()
        except subprocess.CalledProcessError as err:
            raise Exception("'%s' command execution failed" % (' '.join(cmd)))

    @classmethod
    def run_script(cls, script, *args, **kwargs):
        try:
            cmd = []
            if kwargs.get('sudo'):
                cmd.append('sudo')
            cmd.append(script)
            for a in args:
                cmd.append(a)
            logger.info("Executing the '%s' script...", script)
            outt, err = cls._cmd_async(cmd)
            return outt, err
        except Exception as err:
            logger.debug(err)
            raise Exception("Failed to execute the '%s' script" % script)

    @classmethod
    def change_os_password(cls, username, password):
        try:
            cmd = "%s %s:%s | %s %s" % (
                cls.get_package_path('echo'),
                username,
                password,
                cls.get_package_path('sudo'),
                cls.get_package_path('chpasswd'))
            out, err = cls.run_cmd(cmd)
            if err:
                logger.debug(err)
                logger.warning(
                    "Unable to change the user:'%s' password", username)
                return False
            return True
        except Exception as err:
            logger.debug(err)
            raise

    @classmethod
    def list_net_ns(cls):
        try:
            ip = cls.get_package_path('ip')
            return cls._cmd_sync(ip, 'netns').split()
        except Exception as err:
            logger.debug(err)
            raise Exception("Failed to fetch the network namespaces")

    @classmethod
    def ping_host(cls, host, count=10, byte_size=56):
        try:
            logger.debug(
                "Pinging host '%s'. Count is set to '%d' and size is set to '%d'",
                host, count, byte_size)
            output = cls._cmd_sync(
                '/bin/ping', '-c', str(count), '-s', str(byte_size), host)
            logger.debug("Ping successful")
            output = output.split('\n')
            rx = re.search(r"transmitted,\s(\d+)", output[-2]).group(1)
            delay = output[-1].split('=')[1].split('/')[1]
            logger.debug(
                "Transmitted packets=%d, received packets=%s, avg rtt=%s",
                count, rx, delay)
            return True
        except subprocess.CalledProcessError as err:
            logger.warning("Host '%s'unreachable", host)
            logger.debug(err)
            return False

    @classmethod
    def get_file(cls, url, path, name=None):
        try:
            path = os.path.abspath(path)
            cls._create_dir(path)
            if not name:
                name = cls._random_str()
            path = os.path.join(path, name)
            if os.path.exists(path):
                logger.debug("'%s' file already exisits", name)
                return True
            logger.debug("Downloading file from '%s'", url)
            response = urlopen(url)
            with open(path, 'w') as f:
                f.write(response.read())
            logger.debug(
                "Download successful. Saved to '%s'", path)
            return True
        except HTTPError:
            raise
        except URLError:
            logger.error("Invalid URL '%s'", url)
            raise
        except OSError:
            raise

    @classmethod
    def get_current_directory(cls):
        # return cls._cmd_sync('pwd')
        return os.getcwd()

    @classmethod
    def get_home_directory(cls):
        return os.path.expanduser('~')

    @classmethod
    def join_paths(cls, *paths):
        p = None
        for path in paths:
            p = os.path.join(p, path)
        return p

    @classmethod
    def check_file(cls, path):
        if os.path.exists(path):
            logger.debug("'%s' file already exisits", path)
            return True
        return False

    @classmethod
    def get_username(cls):
        # return cls._cmd_sync('whoami')
        return socket.gethostname()

    @classmethod
    def get_package_path(cls, pkg):
        try:
            return cls._cmd_sync('which', pkg).strip()
        except Exception as err:
            logger.debug(err)
            raise Exception(
                "'%s' package doesn't exist" % pkg)

    @classmethod
    def get_ip_range(cls, cidr, gw, count):
        try:
            socket.inet_aton(gw)
            cidr = ipaddress.ip_network(unicode(cidr))
            hosts = list(cidr.hosts())
            assert int(count) < len(hosts), "Requested range is greater than available IPs"
            for ip in hosts:
                if str(ip) == unicode(gw):
                    if len(hosts[:hosts.index(ip)]) >= int(count):
                        return str(hosts[0]), str(hosts[int(count)-1])
                    elif len(hosts[hosts.index(ip)+1:]) >= int(count):
                        return str(hosts[hosts.index(ip)+1]), str(hosts[hosts.index(ip)+int(count)])
                    else:
                        raise Exception("Gateway IP conflicts with IP Pool")
                    #assert len(hosts[hosts.index(ip):]) > int(pool_count), "Gateway IP conflicts with IP Pool"
                    #return str(hosts[hosts.index(ip)+1]), str(hosts[int(count)])
        except socket.error as err:
            logger.debug(err)
            raise
        except AssertionError as err:
            logger.debug(err)
            raise
        except Exception as err:
            logger.debug(err)
            raise

    @classmethod
    def get_dnssec_key(cls):
        try:
            logger.info("Creating DNS security key")
            return cls.run_cmd("head -c 64 /dev/random | base64 -w 0")[0]
        except Exception as err:
            logger.debug(err)
            raise Exception("Failed to create DNS security key")
