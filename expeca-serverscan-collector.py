#!/usr/bin/env python
# install paramiko package: pip3 install paramiko
# Make sure the following entries are in /etc/hosts:
# 10.20.111.1 storage-01
# 10.20.111.2 worker-01
# 10.20.111.5 worker-02
# 10.20.111.6 worker-03
# 10.20.111.7 worker-04
# 10.20.111.3 worker-05
# 10.20.111.4 worker-06
# 10.20.111.8 worker-07
# 10.20.111.9 worker-08
# 10.20.111.10 worker-09
# 10.20.111.11 worker-10
# Run this on openstack controller:
# curl -LJO https://raw.githubusercontent.com/KTH-EXPECA/admin-tools/main/scan-internal.py
# python3 scan-control.py

import socket
import subprocess
import sys
import paramiko
from datetime import datetime
import json
import os


os.chdir(sys.path[0])      # Set current directory to script directory


USER = 'expeca'
SSHKEY = '/home/expeca/.ssh/id_rsa.pub'

# Define hosts to scan
hosts = {
    'storage-01' : {
        'port' : 22
    },
    'worker-01' : {
        'port' : 22
    },
    'worker-02' : {
        'port' : 22
    },
    'worker-03' : {
        'port' : 22
    },
    'worker-04' : {
        'port' : 22
    },
    'worker-05' : {
        'port' : 22
    },
    'worker-06' : {
        'port' : 22
    },
    'worker-07' : {
        'port' : 22
    },
    'worker-08' : {
        'port' : 22
    },
    'worker-09' : {
        'port' : 22
    },
    'worker-10' : {
        'port' : 22
    }                       
}                             
                              
# Print a nice banner with information on which host we are about to scan
# print("-" * 100)
# print ("{:<20} {:<20} {:<10} {:<10} {:<15} {:<20}".format('HOST','IP','PORT','STATUS','SSH', 'PASSWORD'))

outp_list = []

for host in hosts:                                                       
    remoteServer = host                                                  
    port = hosts[host]['port']                                           
                                                                         
    # print("-" * 100)
                                                                         
    # We also put in some error handling for catching errors             
    try:                                                                 
        remoteServerIP  = socket.gethostbyname(remoteServer)             
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         
        sock.settimeout(0.5)                                             
        result = sock.connect_ex((remoteServerIP, port))                 
        sock.close()      

        if result == 0:                                                  
            resStr = 'Up'                                                
        else:                                                            
            resStr = 'Down'                                              
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(remoteServerIP, username=USER, key_filename=SSHKEY)
            resStrSSH = 'Success'

            stdin, stdout, stderr = ssh.exec_command("sudo -n true")
            result = stdout.channel.recv_exit_status()    # status is 0

            if result == 0:
                resStrSUDO = 'is passwordless'
            else:
                resStrSUDO = 'needs a password'

        except (paramiko.ssh_exception.BadHostKeyException, paramiko.ssh_exception.AuthenticationException,
            paramiko.ssh_exception.SSHException) as e:
            resStrSSH = 'Fail'

    except KeyboardInterrupt:                                            
        print("You pressed Ctrl+C")
        sys.exit()        
    except socket.gaierror:                                              
        remoteServerIP = '-'                                             
        resStr = 'Hostname not found'   
        resStrSSH = '-'                             
        resStrSUDO = '-'                             
    except socket.error:                                                 
        remoteServerIP = '-'                                             
        resStr = 'Could not connect to server'   
        resStrSSH = '-'                             
        resStrSUDO = '-'               
                                                                         
    # print ("{:<20} {:<20} {:<10} {:<10} {:<15} {:<20}".format(remoteServer,remoteServerIP,port,resStr, resStrSSH, resStrSUDO))

    if resStr == "Up":
        status = 1
    else:
        status = 0

    outp = {
        "metric_name": "expeca_server_status",
        "labels": {
            "remoteServer": remoteServer,
            "remoteServerIP": remoteServerIP,
            "port": port,
            "resStr": resStr,
            "resStrSSH": resStrSSH,
            "resStrSUDO": resStrSUDO
        },
        "value": status
    }

    outp_list.append(outp)
                                                                                         
# print("-" * 100)

print(json.dumps(outp_list, indent = 4))
