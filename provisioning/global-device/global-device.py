#!/usr/bin/env python

# coding: utf-8

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# Global IoT Device Provisioning
#
# An example IoT Device for a global device provisioning approach. The device sends it's thing name to an API gateway. If the device has the permssion to be provisioned it get's as a result the region, iot endpoint, private key and certificate.
#
# With this information the device is able to connect to the endpoint where it has been provisioned and may publish data.

import argparse
import base64
import json
import os
import requests
import sys
import time
import uuid
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from OpenSSL import crypto
from OpenSSL.crypto import X509
from time import gmtime, strftime

# globals

# signing key file
priv_key_file = 'global-provisioning.priv.key.pem'
#pub_key_file = 'global-provisioning.pub.key.pem'
#rootCAPath = "root.ca.pem"
rootCAPath = 'root.ca.bundle.pem'


#
# parse command line args
#
parser = argparse.ArgumentParser(description='Sample device for global provisiong with AWS IoT Core')
parser.add_argument("-t", "--thing-name", action="store", required=True, dest="thing_name", help="thing name for your device")
parser.add_argument("-a", "--api-gw", action="store", required=True, dest="api_gw", help="API Gateway URL for device provisioning")
parser.add_argument("-k", "--own-key", action="store_true", dest="use_own_priv_key", default=False,
                    help="Use own private key for the device")
parser.add_argument("-c", "--continue", action="store_true", dest="continue_provisioning", default=False,
                    help="continue the provisioning process without interaction")
parser.add_argument("-f", "--fake-device", action="store_true", dest="fake_device", default=False,
                    help="use a fake device name to demonstrate that verifying the sig fails")

args = parser.parse_args()
thing_name = args.thing_name
api_gw = args.api_gw
use_own_priv_key = args.use_own_priv_key
continue_provisioning = args.continue_provisioning
fake_device = args.fake_device

endpoint = None

def cont():
    if continue_provisioning:
        return
    raw_input("== press <enter> to continue, <ctrl+c> to abort!\n")

# key/cert/csr file name for the thing
key_file = thing_name + '.device.key.pem'
csr_file = thing_name + '.device.csr.pem'
cert_file = thing_name + '.device.cert.pem'
endpoint_file = thing_name + '.endpoint'


if os.path.isfile(key_file) and os.path.isfile(cert_file):
    print("=> device already provisioned")
    f = open(endpoint_file, 'r')
    line = f.readline().rstrip('\n')
    f.close()
    endpoint_region = line.split('::')
    endpoint = endpoint_region[0]
    region = endpoint_region[1]
    print("   endpoint: {}, region: {}".format(endpoint, region))
    cont()
else:
    print("=> provisioning device with AWS IoT Core...")
    print("   thing-name: {}".format(thing_name))
    print("   use_own_priv_key: {}".format(use_own_priv_key))
    cont()

    # ### Create Signature for Thing Name
    # For a valid provisioning request the device must send it's name as well as the sig for the thing name. The signature is created with a private key.
    f = open(priv_key_file, 'r')
    priv_key_pem = f.read()
    f.close()
    priv_key = crypto.load_privatekey(crypto.FILETYPE_PEM, priv_key_pem)
    sig = crypto.sign(priv_key, thing_name, 'sha256')
    sig = base64.b64encode(sig)


    # ### Create a Provisioning Request with own private key and CSR
    # If you want to create the private on your own you can send a CSR together with the provisioning request and let AWS IoT issue the certificate.

    if use_own_priv_key:
        print("=> creating own private key...")
        cont()
        device_priv_key = crypto.PKey()
        device_priv_key.generate_key(crypto.TYPE_RSA, 2048)
        print(crypto.dump_privatekey(crypto.FILETYPE_PEM, device_priv_key))

        file_k = open(key_file,"w")
        file_k.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, device_priv_key))
        file_k.close()

        csr = crypto.X509Req()
        subj = csr.get_subject()
        setattr(subj, "CN", thing_name)
        csr.set_pubkey(device_priv_key)
        csr.sign(device_priv_key, 'sha256')
        print(crypto.dump_certificate_request(crypto.FILETYPE_PEM, csr))

        file_cs= open(csr_file,"w")
        file_cs.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, csr))
        file_cs.close()
    else:
        print("=> using private key from AWS IoT")


    if fake_device:
        print("=> faking device name")
        thing_name = str(uuid.uuid4())

    payload = {'thing-name': thing_name, 'thing-name-sig': sig}
    if use_own_priv_key:
        payload = {'thing-name': thing_name, 'thing-name-sig': sig, 'CSR': crypto.dump_certificate_request(crypto.FILETYPE_PEM, csr)}

    print("=> request payload that will be send to the API Gateway...")
    print("   api gateway url: {}".format(api_gw))
    print("   payload: {}".format(payload))
    cont()

    # ### Send Provisioning Request
    # Send the provisioning request to an API Gateway. The API Gateway will call a Lambda which provisions the device.
    print("=> sending request to API Gateway...")
    r = requests.post(api_gw, data=json.dumps(payload))
    print("<= headers: {}".format(r.headers))
    print("<= text: {}".format(r.text))
    status = r.json()["status"]
    if status == "error":
        print("<= error: device not provisioned")
        sys.exit()
    cont()


    # ### Return Values
    # Testing some return values from the provisioning request.

    region = r.json()["region"]
    endpoint = r.json()["endpointAddress"]
    print("<= region: {}".format(region))
    print("<= endpoint: {}".format(endpoint))
    print("<= certificatePem:\n{}".format(r.json()["certificatePem"]))

    if not use_own_priv_key:
        print("<= PrivateKey\n{}".format(r.json()["PrivateKey"]))


    # ### Store Key and Certificate
    # Write key and certificate to file.

    print("=> writing cert/key to file...")
    file_c = open(cert_file,"w")
    file_c.write(r.json()["certificatePem"])
    file_c.close()

    if not use_own_priv_key:
        file_k = open(key_file,"w")
        file_k.write(r.json()["PrivateKey"])
        file_k.close()

    file_e = open(endpoint_file,"w")
    file_e.write(endpoint + '::' + region)
    file_e.close()


print("=> device is ready to communicate with AWS IoT...")
cont()

host = endpoint
certificatePath = cert_file
privateKeyPath = key_file
clientId = thing_name
topic = "data/" + thing_name + "/misc"


myAWSIoTMQTTClient = None
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, 8883)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
if myAWSIoTMQTTClient.connect():
    print("<= device connected to AWS IoT in region: {}".format(region))
    print("   before you continue subscribe in the AWS IoT console to the topic: {}".format(topic))
    cont()
else:
    print("error: device could not connect to AWS IoT in region: {}".format(region))
    print("       check logs, thing, certificate, key, policy")
    sys.exit()



# ### Publish a message
# **Before you publish a message to the AWS IoT Console and subcribe to "data/#"**. The device publishes a message. If everthing went well during the registration process the message should be seen in the AWS IoT Console.
print("=> start publishing... press <ctrl+c> to abort")

while True:
    message = {"thing-name": thing_name, "global": "device provisioning",
               "datetime": time.strftime("%Y-%m-%dT%H:%M:%S", gmtime())}
    print ("=> publishing message: {}".format(message))
    myAWSIoTMQTTClient.publish(topic, json.dumps(message, indent=4), 0)
    time.sleep(2)


# This message should not arrive because the policy in this example allows the device only to publish to "data/${iot:
# ClientId}/#'

# In[ ]:


#myAWSIoTMQTTClient.publish('other/topic', json.dumps(message, indent=4), 0)
