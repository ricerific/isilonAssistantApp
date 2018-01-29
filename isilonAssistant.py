#!/usr/bin/env python

import http.client
import json
import base64
import sys
import traceback
import ssl
import re
import argparse
import pyautogui
from time import sleep
import subprocess


## Global settings
# Set pyautogui parameters
pyautogui.PAUSE = 1
# Set SSL parameters
ssl._create_default_https_context = ssl._create_unverified_context

	
## The following utility class starts and ends OneFS API sessions
# This class enables you to store a cookie with a session ID for authentication instead of sending your username and password with every request, as with HTTP Basic Authentication.
class ConfigAPISession(object):
    def __init__(self, config_kvp):
        # Session authorization cookie
        self.isisessid = None
        # Credentials for Isilon system
        self.HOST = config_kvp["ext-1_IPLow"]
        self.USER = config_kvp["Cluster_Username"]
        self.PASSWORD = config_kvp["Cluster_Password"]
        self.PORT = config_kvp["Cluster_Port"]
        # URIs for Isilon API
        self.SESSION_URI = config_kvp["API_SessionURI"]
        self.NFS_EXPORTS_URI = config_kvp["API_NFSExportURI"]
        self.CLUSTER_ADDNODE_URI = config_kvp["API_ClusterAddNodeURI"]

    # Parse isisessid (the OneFS session ID) from the session URI response headers.
    @staticmethod
    def extract_session_id(response_headers):
        isisessid = None
        cookie_header = None
        for h in response_headers:
            if h[0].lower() == "set-cookie":
                cookie_header = h[1]
            if cookie_header:
                cookie_strs = cookie_header.split(";")
                for cs in cookie_strs:
                    nv = cs.split("=")

                    if len(nv) > 1:
                        if nv[0].strip().lower() == "isisessid":
                            isisessid = nv[1].strip()
        return isisessid

    # Create a new session by querying the session URI with your log in credentials.
    def create_session(self):

        headers = {"content-type": "application/json"}
        #headers["Authorization"] = "Basic cm9vdDph"
        #headers["Authorization"] = "Basic " + string.strip(base64.encodestring(USER + ":" + PASSWORD))

        body = json.dumps({"username": self.USER, "password": self.PASSWORD, "services": ["platform", "namespace"]})

        uri = self.SESSION_URI

        print ("- DEBUG: ConfigAPISession.create_session().connection.connect:", self.HOST, self.PORT)
        connection = http.client.HTTPSConnection(self.HOST, self.PORT)
        connection.connect()

        try:
            print ("- DEBUG: ConfigAPISession.create_session().connection.request:", "POST", uri, body, headers)
            connection.request("POST", uri, body, headers)
            response = connection.getresponse()
            self.isisessid = ConfigAPISession.extract_session_id(response.getheaders())
            print ("- DEBUG: ConfigAPISession.create_session().connection.isisessid:",self.isisessid)
        except Exception as e:
            print (e)
            connection.close()
        except http.client.BadStatusLine as e:
            print (e)
            connection.close()

    # End your session with a DELETE request to the session URI.
    def close_session(self):
        uri = self.SESSION_URI
        headers = {}
        headers["Cookie"] = "isisessid=" + self.isisessid

        print ("- DEBUG: ConfigAPISession.close_session().connection.connect:", self.HOST, self.PORT)
        connection = http.client.HTTPSConnection(self.HOST, self.PORT)
        connection.connect()

        try:
            print ("- DEBUG: ConfigAPISession.close_session().connection.request:", "DELETE", uri, "", headers)
            connection.request("DELETE", uri, "", headers)
            response = connection.getresponse()
        except Exception as e:
            print (e)
            connection.close()
        except http.client.BadStatusLine as e:
            print (e)
            connection.close()

        self.isisessid = None

    def send_request(self, method, uri, headers, body):
        response = None
        headers["Cookie"] = "isisessid=" + str(self.isisessid)

        print ("- DEBUG: ConfigAPISession.send_request().connection.connect:", self.HOST, self.PORT)
        connection = http.client.HTTPSConnection(self.HOST, self.PORT)
        connection.connect()

        try:
            print ("- DEBUG: ConfigAPISession.send_request().connection.request:", method, uri, body, headers)
            connection.request(method, uri, body, headers)
            response = connection.getresponse()
        except Exception as e:
            print (e)
            connection.close()
        except http.client.BadStatusLine as e:
            print (e)
            connection.close()

        return response

## Print HTTP response error message
def print_errors(response_json):
    if response_json.has_key("errors"):
        errors = response_json["errors"]
        for e in errors:
            print (e["message"])

## Validate HTTP request
def send_request_and_validate(api_session, method, uri, headers, body):
    response = api_session.send_request(method, uri, headers, body)
    response_body = response.read()

    print ("- DEBUG: send_request_and_validate().response_body:", response_body)
    
    response_json = None
    if response_body != None and response_body.decode('UTF-8') != "":
        response_json = json.loads(response_body)

    # The status code must be set to 2XX, otherwise an error will occur.
    if response.status < 200 or response.status >= 300:
        print ("Error:", response.status, method, uri)
        if response_json != None:
            print_errors(response_json)
            raise Exception("Response status: " + str(response.status))

    return response_json

## Perform keyboard to Isilon Console
def operateIsilonConsole(config_kvp):

    ## Move mouse cursor to Isilon console
    coordinateX = int(config_kvp["Console_CoordinateX"])
    coordinateY = int(config_kvp["Console_CoordinateY"])

    print ("- Console coordinates:", coordinateX, ",", coordinateY)
    pyautogui.moveTo(coordinateX, coordinateY, duration = 5)
    pyautogui.click(coordinateX, coordinateY)
    
    ## Begin keyboard operations
    # Assumption: console is at the wizard page, no SmartConnect, no DNS, no timezone
    print ("- Begin keyboard sequence")
    # 1	[Enter] > Create new cluster
    pyautogui.typewrite(["1", "enter"])
    # q > Quit EULA
    pyautogui.press("q")
    # yes [Enter] > Accept EULA
    pyautogui.typewrite("yes")
    pyautogui.press("enter")
    # a	[Enter] > Root password
    pyautogui.typewrite(config_kvp["Cluster_Password"])
    pyautogui.press("enter")
    # a	[Enter] > Root password
    pyautogui.typewrite(config_kvp["Cluster_Password"])
    pyautogui.press("enter")
    # a	[Enter] > Admin password
    pyautogui.typewrite(config_kvp["Cluster_Password"])
    pyautogui.press("enter")
    # a	[Enter] > Admin password
    pyautogui.typewrite(config_kvp["Cluster_Password"])
    pyautogui.press("enter")
    # c1 [Enter]	> Cluster name
    pyautogui.typewrite(config_kvp["Cluster_Name"])
    pyautogui.press("enter")
    # [Enter] > Skip/Accept current encoding: utf-8 && Enter int-a IP settings
    pyautogui.press("enter")
    # 1	[Enter] > Configure int-a netmask
    pyautogui.typewrite(["1", "enter"])
    # 255.255.255.0	[Enter] > Input int-a netmask
    pyautogui.typewrite(config_kvp["int-a_Netmask"])
    pyautogui.press("enter")
    # 3	[Enter] > Configure int-a IP range
    pyautogui.typewrite(["3", "enter"])
    # 1	[Enter] > Add int-a IP range
    pyautogui.typewrite(["1", "enter"])
    # 192.168.20.10	[Enter] > Input int-a low IP address
    pyautogui.typewrite(config_kvp["int-a_IPLow"])
    pyautogui.press("enter")
    # 192.168.20.19	[Enter] > Input int-a high IP address (backspace 15 times before input)
    pyautogui.typewrite(["backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace"])
    pyautogui.typewrite(config_kvp["int-a_IPHigh"])
    pyautogui.press("enter")
    # [Enter] > Accept int-a low+high IP range
    pyautogui.press("enter")
    # [Enter] > Accept int-a IP settings
    pyautogui.press("enter")
    # [Enter] > Skip int-b IP settings
    pyautogui.press("enter")
    # 1	[Enter] > Enter ext-1 IP settings
    pyautogui.typewrite(["1", "enter"])
    # 1	[Enter] > Configure ext-1 netmask
    pyautogui.typewrite(["1", "enter"])
    # 255.255.255.0	[Enter] > Input ext-1 netmask
    pyautogui.typewrite(config_kvp["ext-1_Netmask"])
    pyautogui.press("enter")
    # 3	[Enter] > Configure ext-1 IP range
    pyautogui.typewrite(["3", "enter"])
    # 1	[Enter] > Add ext-1 IP range
    pyautogui.typewrite(["1", "enter"])
    # 192.168.10.10 [Enter] > Input ext-1 low IP address
    pyautogui.typewrite(config_kvp["ext-1_IPLow"])
    pyautogui.press("enter")
    # 192.168.10.19	[Enter] > Input ext-1 high IP address (backspace 15 times before input)
    pyautogui.typewrite(["backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace", "backspace"])
    pyautogui.typewrite(config_kvp["ext-1_IPHigh"])
    pyautogui.press("enter")
    # [Enter] > Accept ext-1 low+high IP range
    pyautogui.press("enter")
    # [Enter] > Accept ext-1 IP settings
    pyautogui.press("enter")
    # 192.168.10.2 [Enter]	> Input ext-1 default gateway
    pyautogui.typewrite(config_kvp["DefaultGateway"])
    pyautogui.press("enter")
    # [Enter] > Skip/Accept current SmartConnect IP settings
    pyautogui.press("enter")
    # [Enter] > Skip/Accept current DNS settings
    pyautogui.press("enter")
    # [Enter] > Enter date/time settings
    pyautogui.press("enter")
    # [Enter] > Skip/Accept current date/time settings
    pyautogui.press("enter")
    # [Enter] > Skip/Accept current Cluster Join Mode = Manual
    pyautogui.press("enter")
    # yes [Enter] > Accept cluster settings && Build cluster
    pyautogui.typewrite("yes")
    pyautogui.press("enter")
    print ("- End keyboard sequence")
    
    ## Check node reboot process
    # Wait for node to reboot
    print ("- Wait for node to reboot: 60s")
    sleep (60)
    # Perform node ping test
    pingIP = subprocess.Popen(["ping","-n","5",config_kvp["ext-1_IPLow"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pingOutput = pingIP.communicate()[0]
    pingCode = pingIP.returncode
    print("- DEBUG: operateIsilonConsole.subprocess.Popen.communicate():", pingOutput)
    if pingCode == 0:
            print ("- Node", config_kvp["ext-1_IPLow"], "is reachable")
            return 0
    else:
            print ("- Node", config_kvp["ext-1_IPLow"], "is not reachable")
            return 1
	

## Perform calls to Isilon API
# Cluster operations: add nodes
# NFS operations: list export, create export
def operateIsilonAPI(config_kvp):
    api_session = ConfigAPISession(config_kvp)
    api_session.create_session()

    try:
        ## Perform Cluster operations
        # Assumption: there are 2 nodes available for add
        print ("- Cluster operations:")
        collection_uri = api_session.CLUSTER_ADDNODE_URI

        # Add nodes to cluster
        print ("- Cluster operations: Add node", config_kvp["Serial_Node2"])
        post_body = {"serial_number": config_kvp["Serial_Node2"]}
        response_json = send_request_and_validate(api_session, "POST", collection_uri, {}, json.dumps(post_body))

        print ("- Wait for node to reboot: 60s")
        sleep (60)
        
        print ("- Cluster operations: Add node", config_kvp["Serial_Node3"])
        post_body = {"serial_number": config_kvp["Serial_Node3"]}
        response_json = send_request_and_validate(api_session, "POST", collection_uri, {}, json.dumps(post_body))

        print ("- Wait for node to reboot: 60s")
        sleep (60)
        
        ## Perform NFS operations
        # Assumption: the user sending the request must have the ISI_PRIV_NFS privilege.
        print ("- NFS operations:")
        collection_uri = api_session.NFS_EXPORTS_URI

        # List all exports
        print ("- NFS operations: List all exports")
        response_json = send_request_and_validate(api_session, "GET", collection_uri, {}, "")
        print (json.dumps(response_json, indent=4))

        # Create an export
        # Assumption: export path exists on your system, map_root = root, description = Hello Paul
        print ("- NFS operations: Create an export", config_kvp["NFS_Export1"])
        post_body = {"paths": [config_kvp["NFS_Export1"]], "description": "Hello Paul", "map_root": {"enabled": True, "primary_group": {}, "secondary_groups": [], "user": {"id": "USER:root"}}}
        response_json = send_request_and_validate(api_session, "POST", collection_uri, {}, json.dumps(post_body))

        item_id = response_json["id"]
        item_uri = collection_uri + "/" + str(item_id)
        print ("- Successfully created export with id:", item_id)

        # List newly created export
        response_json = send_request_and_validate(api_session, "GET", item_uri, {}, "")

        print ("- Value for export id:", response_json["exports"][0]["id"])
        print ("- Value for export description:", response_json["exports"][0]["description"])
        print ("- Value for export path:", response_json["exports"][0]["paths"])
        
    except:
        traceback.print_exc(file=sys.stdout)
        return 1

    api_session.close_session()

    return 0

def main():
	
    ## Check command line arguments
    usage = "usage: %prog [options]"
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", action="store", dest="file", required=True, help="config file to parse")
    args=parser.parse_args()
    
    ## Read JSON config file into key/value hash dictionary
    conf_file=args.file
    config_kvp=dict()
    
    try:
            fh=open(conf_file, 'r')
            config_kvp=json.load(fh)
            
            print ()
            print ("Load Hash Dictionary...")
            for key in config_kvp:
                    print("-", key, ":", config_kvp[key])
            print ("SUCCESS: loadHashDictionary")
            
    except Exception as e:
            print (e)
            print ("FAILED: loadHashDictionary")
            sys.exit(1)
    
    ## Configure Isilon Console
    print ()
    print ("Configure Isilon Console...")
    if operateIsilonConsole(config_kvp) == 0:
    	print("SUCCESS: operateIsilonConsole")
    else:
    	print ("FAILED: operateIsilonConsole")
    	sys.exit(1)
    
    ## Configure Isilon API
    print ()
    print ("Configure Isilon API...")
    if operateIsilonAPI(config_kvp) == 0:
        print ("SUCCESS: operateIsilonAPI")
    else:
        print ("FAILED: operateIsilonAPI")
        sys.exit(1)

    return 0

if __name__ == "__main__":
    main()
