#!/bin/bash

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

# create-root-ca-bundle.sh
# creates a file containing all the CAs that could be
# used to sign an AWS IoT server certificate
# See also: https://docs.aws.amazon.com/iot/latest/developerguide/managing-device-certs.html

ROOT_CA_FILE=root.ca.bundle.pem

cp /dev/null $ROOT_CA_FILE

for url in 'https://www.amazontrust.com/repository/AmazonRootCA1.pem' \
    'https://www.amazontrust.com/repository/AmazonRootCA2.pem' \
    'https://www.amazontrust.com/repository/AmazonRootCA3.pem' \
    'https://www.amazontrust.com/repository/AmazonRootCA4.pem' \
    'https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem'
do
    echo $url
    wget -O - $url >> $ROOT_CA_FILE
done
