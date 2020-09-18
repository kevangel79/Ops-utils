#!/usr/bin/env python3

import json, sched, time
import subprocess
import argparse
from ServiceRegistryAms import PullPublish

def init_ams_agent():
    with open("config.json") as json_data_file:
        config = json.load(json_data_file)
    return PullPublish(config)

def update_data( registries, messages ):
    new_registries = []
    for msg in messages:
        is_reconfiguration = False
        for registry in registries:
            if registry['registry_service_id'] == msg['id']:
                is_reconfiguration = True                
                registry['whitelist'] = [ msg['entity_id'] ]
                registry['src'] = msg['metadata_url']
                break
        if is_reconfiguration == False:
            new_registries.append({'registry_service_id': msg['id'], 'whitelist': [msg['entity_id']], 'src': msg['metadata_url']})
    return registries + new_registries

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
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', required=True, type=str, help="Provide the path of the ssp metadata configuration file")
    args = parser.parse_args()
    path = args.c
    ams = init_ams_agent()
    registries_data = subprocess.run(['php','./utils/json_export.php', path], universal_newlines=True, stdout=subprocess.PIPE)
    registries_json = json.loads(registries_data.stdout)
    #messages = ams.pull(1) # Get messages
    messages = [{'id': 666, 'service_name': 'Saml reconfigure name', 'service_description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean in ex in tellus congue commodo. Suspendisse condimentum purus ante, in ornare leo egestas ut.', 'logo_uri': 'https://cdn.auth0.com/blog/duo-saml-exploit/saml.png', 'policy_uri': 'https://policy_uri.com', 'integration_environment': 'demo', 'protocol': 'saml', 'metadata_url': 'https://metadataurl.com', 'entity_id': 'https://saml-id-1_reconfigure.com', 'deleted': False, 'contacts': [{'email': 'mygrail@gmail.com', 'type': 'admin'}, {'email': 'myfail@gmail.com', 'type': 'admin'}]}, {'id': 8, 'service_name': ' Registration Service', 'service_description': 'https://dcassetcdn.com/design_img/2772494/655674/655674_15180795_2772494_df327367_image.jpg', 'logo_uri': 'https://dcassetcdn.com/design_img/2772494/655674/655674_15180795_2772494_df327367_image.jpg', 'policy_uri': 'https://dcassetcdn.com/design_img/2772494/655674/655674_15180795_2772494_df327367_image.jpg', 'integration_environment': 'demo', 'protocol': 'saml', 'metadata_url': 'https://metadata.com', 'entity_id': 'https://entity_id.com', 'deleted': False, 'contacts': [{'email': 'asdasdasda@asdfsadf.com', 'type': 'admin'}]}]
    messages_counter = len(messages)
    while len(messages)>0:
        registries_json = update_data(registries_json, messages)
        messages = ams.pull(1)
        messages_counter += len(messages)
    if messages_counter > 0:
        generate_config(registries_json, path)
        #subprocess.run(['curl','http://localhost/proxy/module.php/cron/cron.php?key=TOPSECRET&tag=hourly'])
