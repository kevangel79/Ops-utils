#!/usr/bin/env python3

import ipaddress
import subprocess
import csv
import os

os.chdir('/var/cache/iciimport')

# Download argo inventory csv file
download_argo_csv=['wget', '--no-check-certificate', '-O', '/var/cache/iciimport/argo_mon_hosts.csv', 'https://docs.google.com/spreadsheets/d/10mqY1qdBPBBlLGJYPeV2fpQhPa6nCeVWhll3OQKemoM/export?gid=2117914515&format=csv']
subprocess.run(download_argo_csv)

# Download aai inventory csv file
download_aai_csv=['wget', '--no-check-certificate', '-O', '/var/cache/iciimport/rciam_hosts.csv', 'https://docs.google.com/spreadsheets/d/1m4C9q2SLegZa4xqvz0Hwp6JbOGRmOP_RFvubnSV6WFM/export?gid=1863768075&format=csv']
subprocess.run(download_aai_csv)

# Check for file changes
aai_changed=False
argo_changed=False
status_output=subprocess.run(['git','status', '--short', 'argo_mon_hosts.csv', 'rciam_hosts.csv'],universal_newlines=True, stdout=subprocess.PIPE)

changed_files = status_output.stdout.split('\n')
for file in changed_files:
    file_status=file.split()
    if (len(file_status)!=0):
        if (file_status[1]=='argo_mon_hosts.csv'):
            if (file_status[0] == 'M'):
                argo_changed=True
        if (file_status[1]=='rciam_hosts.csv'):
            if (file_status[0] == 'M'):
                aai_changed=True
if argo_changed == False and aai_changed==False:
    print('>>> No changes detected')
    exit(0)

# Verify IPv4 is set properly
argo_valid=True
aai_valid=True
if argo_changed == True:
    with open('./argo_mon_hosts.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                ipv4_index = row.index('ipv4')
                line_count += 1
            else:
                try:
                    ipaddress.ip_address(row[ipv4_index])
                except:
                    argo_valid=False

if aai_changed == True:
    with open('./rciam_hosts.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                ipv4_index = row.index('ipv4')
                line_count += 1
            else:
                try:
                    ipaddress.ip_address(row[ipv4_index])
                except:
                    aai_valid=False

if argo_valid == False or aai_valid == False:
    print('>>> Invalid IP')
    print('>>> Reset files to last commit') 
    subprocess.run(['git','reset', '--hard'])
    exit(1)

# Commit changes
print('>>> Adding new commit')        
subprocess.run(['git','add', './argo_mon_hosts.csv', './rciam_hosts.csv'])
subprocess.run(['git','commit','-m', 'Save Files'])

# Run Icinga import
print('>>> Run icinga import') 
subprocess.run(['icingacli', 'director', 'importsource', 'run', '--id', '9'])
subprocess.run(['icingacli', 'director', 'importsource', 'run', '--id', '14'])

# Run Icinga syncrule
print('>>> Run icinga sync') 
subprocess.run(['icingacli', 'director', 'syncrule', 'run', '--id', '9'])
subprocess.run(['icingacli', 'director', 'syncrule', 'run', '--id', '4'])


# Deploy changes
print('>>> Run icinga deploy') 
subprocess.run(['icingacli', 'director', 'config', 'deploy'])
