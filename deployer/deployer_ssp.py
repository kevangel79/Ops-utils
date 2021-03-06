#!/usr/bin/env python3

import json, sched, time
import subprocess
import os
import argparse
from ServiceRegistryAms import PullPublish

def init_ams_agent():
    with open("config.json") as json_data_file:
        config = json.load(json_data_file)
    return PullPublish(config)

'''
This function will return the altered current state and new additions to it
    update_data gets 2 arguments:
    
    - registries, which represents the current state in json
    - messages, the new incoming messages in json
'''
def update_data( registries, messages ):
    new_registries = []
    for msg in messages:
        new_entry = True
        for registry in registries:
            if registry['registry_service_id'] == msg['id']:
                new_entry = False
                if msg['deleted'] == False:      
                    registry['whitelist'] = [ msg['entity_id'] ]
                    registry['src'] = msg['metadata_url']
                else:
                    registries.remove(registry)
                break
        if new_entry == True:
            new_registries.append({'registry_service_id': msg['id'], 'whitelist': [msg['entity_id']], 'src': msg['metadata_url']})
    return registries + new_registries

'''
This function get the current state and will generate a configuration
php file with the updated state
    generate_config gets 2 arguments:
    - registries, which represents the current state in json
    - path, which is the location of the config file
'''
def generate_config( registries, path ):
    header = """<?php
return array("""
    footer = """
);"""
    content = ""
    for registry in registries:
        content += """
    array(
        'registry_service_id' => """ + str(registry['registry_service_id']) + """,
        'whitelist' => array (
            '"""+ str(registry['whitelist'][0])  +"""',
        ),
        'src' => '""" + str(registry['src']) + """',
    ),"""
    f = open(path,"w")
    f.write(header+content+footer)
    f.close()
    

if __name__ == '__main__':
    # Get config path from arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', required=True, type=str, help="Provide the path of the ssp metadata configuration file")
    args = parser.parse_args()
    path = args.c

    ams = init_ams_agent()
    # Get current registries
    registries_data = subprocess.run(['php','./utils/json_export.php', path], universal_newlines=True, stdout=subprocess.PIPE)
    registries_json = json.loads(registries_data.stdout)
    messages = ams.pull(1) # Get messages
    messages_counter = len(messages)
    while len(messages)>0:
        registries_json = update_data(registries_json, messages)
        messages = ams.pull(1)
        messages_counter += len(messages)
    if messages_counter > 0:
        generate_config(registries_json, path)
        secret_key=os.environ['SECRET_KEY']
        subprocess.run(['echo','http://localhost/proxy/module.php/cron/cron.php?key='+secret_key+'&tag=hourly'])
