# Global IoT Device Provisioning

This repository contains the sample implementation for AWS Global IoT Device Provisioning. The architecture and how the solution works has been published in the [AWS IoT Blog](https://aws.amazon.com/blogs/iot/provision-devices-globally-with-aws-iot/).

This document will guide you to the process to setup the required AWS resources. A virtual device is provided which can be used to test the sample implementation.

The setup has been tested on an EC2 Instance with Amazon Linux AMI [amzn-ami-hvm-2017.03.1.20170812-x86_64-gp2](https://docs.aws.amazon.com/lambda/latest/dg/current-supported-versions.html). Most of the resources will be deployed through an AWS CloudFormation stack. Some preparation is required before the stack can be launched.

## Architecture
![IoT_Global_Device_Provisioning.jpg](IoT_Global_Device_Provisioning.jpg)

## Create the environment

1. To lookup the geo location for the device's IP address [ipstack.com](https://ipstack.com/) is used in this example implementation. To use API from [ipstack.com](https://ipstack.com/) an API Access Key is required. To get your API Access Key follow the sign up steps at [ipstack.com](https://ipstack.com/). The Lambda function which determines the best region will get the API Access Key from an [environment variable](https://docs.aws.amazon.com/lambda/latest/dg/env_variables.html).

2. Launch an EC2 instance with Amazon Linux AMI [amzn-ami-hvm-2017.03.1.20170812-x86_64-gp2](https://docs.aws.amazon.com/lambda/latest/dg/current-supported-versions.html), ssh into the instance and clone the repository from github into your home directory.

		git clone https://github.com/aws-samples/aws-iot-global-device-provisioning.git

3. Create a rsa key pair in the directory `aws-iot-global-device-provisioning/provisioning`

	    cd ~/aws-iot-global-device-provisioning/provisioning
	    openssl genrsa -out global-provisioning.priv.key.pem 2048
	    openssl rsa -in global-provisioning.priv.key.pem -outform PEM -pubout -out global-provisioning.pub.key.pem

4. Upgrade pip if the latest version

	    sudo pip install --upgrade pip
	    hash -r

5. Install required libraries for the Lambda function into the directory `lambda`. If you get warnings about requirements for cloud-init during the installation with pip you can safely ignore them

	    cd lambda
	    pip install -r requirements.txt -t .

6. Copy the public key into the directory where the Lambda is located

    	cp ../global-provisioning.pub.key.pem .

7. Create an installation package for the Lambda function

    	zip ../iot-global-provisioning.zip -r .

8. The Lambda function will be created by CloudFormation an the CloudFormation template expects the installation package to be present in a S3 bucket that must be located in the **same region** where the CloudFormation stack will be launched. By using the awscli to create a bucket and upload the Lambda installation package you would use the following commands:

		aws s3 mb s3://<YOUR_BUCKET_NAME>
		aws s3 cp ../iot-global-provisioning.zip s3://<YOUR_BUCKET_NAME>/
You can also use the AWS Console to create a bucket and upload the installation package.

9. Copy the CloudFormation Template from `aws-iot-global-device-provisioning/provisioning/cfn/cfn-iot-global-device-provisioning.json` into the same S3 bucket. If the awscli is used the command looks similar to:

		cd ..
		aws s3 cp cfn/cfn-iot-global-device-provisioning.json s3://<YOUR_BUCKET_NAME>/

10. Launch the CloudFormation template from the AWS CloudFormation console

    1. Got to the AWS CloudFormation Console
    2. Create Stack
    3. Specify an Amazon S3 template URL: `http://s3-<YOUR_AWS_REGION>.amazonaws.com/<YOUR_BUCKET_NAME>/cfn-iot-global-device-provisioning.json`
    4. Next
    5. Stack name: `IoTGlobalDeviceProvisioning`
    6. IpStackApiKey: `<your-api-access-key-for-ipstack.com>`
    7. S3BucketName: `<YOUR_BUCKET_NAME>`
    8. Next
    9. Next
    10. Check `I acknowledge that AWS CloudFormation might create IAM resources with custom names.`
    11. Create
    12. It should take some minutes for the stack to be created.

11. The DynamoDB table `iot-global-provisioning` that was created by CloudFormation needs to be populated with device names that are allowed to be provisioned. The following command will create 10 devices named `mydevice1 ... mydevice10` in the DynamoDB table and put their provisioning state `prov_status` to `unprovisioned`:

    	for i in 1 2 3 4 5 6 7 8 9 10; do aws dynamodb put-item --table-name iot-global-provisioning --item "{\"prov_status\": {\"S\": \"unprovisioned\"}, \"thing_name\":{\"S\": \"mydevice$i\"}}"; done

12. Scan the DynamoDB table to verify that the entries have been created:

    	aws dynamodb scan --table-name iot-global-provisioning

13. Install python libraries required to run the example global-device

	    cd ~/aws-iot-global-device-provisioning/provisioning/global-device
	    sudo /usr/local/bin/pip install -r requirements.txt

14. Copy the private key you created earlier into the directory where the global device is located

    	cp ../global-provisioning.priv.key.pem .
    	
15. Get the CA certificates the could be used to sign the [AWS IoT server certificates](https://docs.aws.amazon.com/iot/latest/developerguide/managing-device-certs.html)

		./create-root-ca-bundle.sh

## Provision a device
In the previous section you have already configured a virtual device that can be used to demonstrate how the global device provisioning process works. This device is located in `~/aws-iot-global-device-provisioning/provisioning/global-device/global-device.py`. To start this example device you need to provide the API Gateway URL. The device will send provisioning requests to that URL. The API Gateway URL can be retrieved from the outputs section of the CloudFormation stack:

* Go to the AWS CloudFormation console

	1. Click `IoTGlobalDeviceProvisioning`
	2. Expand `Outputs`
	3. You will find the API Gateway URL as `IoTApiGWUrl`


To demonstrate the provisioning process we will provision a device with the name `mydevice3`. The private key will be generated on the device and the corresponding CSR will be used  in the provisioning process. After every major step the virtual device will wait for you to hit <enter> to better comprehend the provisioning process:

Let's get started:

	./global-device.py -t mydevice3 -a https://abcdefg.execute-api.AWS_REGION.amazonaws.com/test/device-provisioning -k

	=> provisioning device with AWS IoT Core...
	 thing-name: mydevice3
	 use_own_priv_key: True
	== press <enter> to continue, <ctrl+c> to abort!

	=> creating own private key...
	== press <enter> to continue, <ctrl+c> to abort!

	-----BEGIN PRIVATE KEY-----
	MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDUSOctOSUtmlVn
	iEorU3vKJtfMYECBdHZdfs72P0797Znw6jnUukP6sRsyiguJmTHDbp4nfvdADMmu
	6mTcRTWFVKOVaJtcG5ay0yb5GT9O0u40DdKiYwkXnES/2t08lhD3cEbkxzsedav9
	vEyu9eJjh72aLvfSr2RBzGmo4FoSbVpAosN0axgwWWU5lAuXXW1Fex6wpFhxyPfC
	gEF1zkZzMvz9f6Y8RGDzmwpmF32pTq2b7i5Pu1OGC0GrCm9rH87gMjE2my9mjxJa
	bKFxwYxjZ9niQz5Y6aq0Ehes487VfFhmbnhQ48huiv0PdDRXc23u3/f92G4G6uSY
	LBapo8q5AgMBAAECggEBAKNTK7mZe8coNIkhTJ8k7drMI7+0VizDY8XvKGBAuQ+Y
	3JWEP9YxMNgRpvEtUE8fNDA+TSPqBWSb8hfHcq4d+V2JjwoGn3EwMLOIzTVdfV2x
	317hO6uAMqCdtC8/vnM8qfUVxxWBSzTWJ+tiEkWSHAmjh/a2KClKlAIjuS8a3XHK
	lZ0GByZ+I2ocZUqxSL3tuxubhBX1pDZehFcllygpVmzxE5QQeCtzWxMorgff+797
	JS799F82rBMgLg0qFtWLIOCbryw55V+ohAE0PzKW5Q+eHdRIqfn+X/bMnbZ0tA52
	aXWJdt3nSALMW9zzipkQ6wUp6EAVFO2HUeeiaMXyFOECgYEA7XOlcg1AKzliEZaV
	lStW+MMK6nm6BMbemKKK1NGGQYRADf2J70yCI+hS/Jy9IiqYPaB8XLtHWfihcuh3
	r3l3HgnAS/Vv0jvDqvSJTgxEkY6Qo52ojKIzHZqj68vBvpvLDyM3AI+x9K8OyVU/
	jUb3K4tonmQOAG+Wo/wckrALRF0CgYEA5N39WPm31lmOHv3FPvktfj2elIfbTC8R
	60F/qdfKpCQmXMrfdyCac4TuYqdBN59f3mEIVsxgqjphXQufXx/m3QfP74LH8fsM
	sp9Zkg3qxRUFH1PQGr8Wrp90OIQeGcEbnLssw1tLpmNqDY+UuYWWUzGIZuxZO6Yx
	mUB1BAyheg0CgYAV2QQqAEodMARz9dUBiqFP9jI07MpO0jV8+ceoWTbvJEn4f5GH
	cRSwVRn9oDZOxHiJgxCuP5ULFDNWrUkF3jk1jFQjKQwG3fTc7+8KPVq5wdJRG5p8
	hhgJ60aV1YOYFCGU3PqclJwdFVZY8/0K9LKdURBpMm+PXrUPlYzTelsvCQKBgQDh
	RSvId0ufHVkJYinS+TrxJj+/3RVaoH4XvMmm6HNaKwbjkQBx5lKAYBiwXAaSdDnN
	zl6B6PtAsuQAzJ7a57C6YKUoD+c0ZDI0Yyqr2yz5Pd5j3oBYwzvVN7gSpOBn4y6F
	j6rYwzTsGrBZlrkB/t5fFsM2425VixkIymwjRzdtxQKBgEDBknh7zEGgo69qIbWV
	YE1rVbVPKJVJsa7+Wx1lfjtxdbSM9Mgi/iuLhKrVhgw9bgAy7byI7/PQZ0f1KK6B
	j9Gifv0FysqFWq8f64ThP1ithLB1KcAWz7dtvv0q8sbBHpXx5Wr0UahuazEagZax
	gOXLODmPkMQa++2PY4O//Kw0
	-----END PRIVATE KEY-----

	-----BEGIN CERTIFICATE REQUEST-----
	MIICWTCCAUECAQAwFDESMBAGA1UEAwwJbXlkZXZpY2UzMIIBIjANBgkqhkiG9w0B
	AQEFAAOCAQ8AMIIBCgKCAQEA1EjnLTklLZpVZ4hKK1N7yibXzGBAgXR2XX7O9j9O
	/e2Z8Oo51LpD+rEbMooLiZkxw26eJ373QAzJrupk3EU1hVSjlWibXBuWstMm+Rk/
	TtLuNA3SomMJF5xEv9rdPJYQ93BG5Mc7HnWr/bxMrvXiY4e9mi730q9kQcxpqOBa
	Em1aQKLDdGsYMFllOZQLl11tRXsesKRYccj3woBBdc5GczL8/X+mPERg85sKZhd9
	qU6tm+4uT7tThgtBqwpvax/O4DIxNpsvZo8SWmyhccGMY2fZ4kM+WOmqtBIXrOPO
	1XxYZm54UOPIbor9D3Q0V3Nt7t/3/dhuBurkmCwWqaPKuQIDAQABoAAwDQYJKoZI
	hvcNAQELBQADggEBAIcA7O+Nw97yJlEmtN6bGoLHkRfsRrL+NNgHv4hHX+eS1EXJ
	O0H8W5CrblYXutmuxPa1+ugNMCB81y6on8T2RZQyiHagnBkLt5hBT+g240/QDZZU
	avrwM8Yo0HtEb8LyoP0mYV4O6jTFRgAAJXPJclNQOtgB+XG5XIf3SvGvL50kDMoY
	zBmszduL9SIKxALNTVOO+/WMMHl/CI3/bUbgmHr9DXynN8McrcNRn9EfkdKPNG4d
	eBf1TyU3c/k/89iWmECoycKschzBPE1c9hp526R/5RMbxx2JzGuFuZO9laYeUFbX
	KnCSFX+mJqdIcBj7GJI+dh0kh2RS9Dbbe3460n0=
	-----END CERTIFICATE REQUEST-----

	=> request payload that will be send to the API Gateway...
	 api gateway url: https://123v76ul4c.execute-api.eu-west-2.amazonaws.com/test/device-provisioning
	 payload: {'thing-name': 'mydevice3', 'thing-name-sig': 'tBQisU1wlLyuolvPSqPT11GswHNUMMlHrAg3FpZq9ZGrI5/c5HxffwWRT1/R0PcTcUg/ewMwB8HX705GsNdz1udbjrtApEoFRaQrDYosej+1fL3dZQeqRzZLqoT7sIRX+AyM8/yaTNom5tmFNwmEdbY8xgR1NePIeURSlVmj5U4RGkQkQDBa/lcy4lSQFAmSd5NPcYLpcDwVr/TxXmGqJxOA/e/r5XobbEve4P2EuVFw7pIbNipljSRSip98yF4F9LzaTw2m/+eemtgsrPX++5/kr7+mST4QHDVK9yO6e9sUMpwyWB0lJ6I/XqwPfPu1acALrttb3gPHBw7gDu6pUA==', 'CSR': '-----BEGIN CERTIFICATE REQUEST-----\nMIICWTCCAUECAQAwFDESMBAGA1UEAwwJbXlkZXZpY2UzMIIBIjANBgkqhkiG9w0B\nAQEFAAOCAQ8AMIIBCgKCAQEA1EjnLTklLZpVZ4hKK1N7yibXzGBAgXR2XX7O9j9O\n/e2Z8Oo51LpD+rEbMooLiZkxw26eJ373QAzJrupk3EU1hVSjlWibXBuWstMm+Rk/\nTtLuNA3SomMJF5xEv9rdPJYQ93BG5Mc7HnWr/bxMrvXiY4e9mi730q9kQcxpqOBa\nEm1aQKLDdGsYMFllOZQLl11tRXsesKRYccj3woBBdc5GczL8/X+mPERg85sKZhd9\nqU6tm+4uT7tThgtBqwpvax/O4DIxNpsvZo8SWmyhccGMY2fZ4kM+WOmqtBIXrOPO\n1XxYZm54UOPIbor9D3Q0V3Nt7t/3/dhuBurkmCwWqaPKuQIDAQABoAAwDQYJKoZI\nhvcNAQELBQADggEBAIcA7O+Nw97yJlEmtN6bGoLHkRfsRrL+NNgHv4hHX+eS1EXJ\nO0H8W5CrblYXutmuxPa1+ugNMCB81y6on8T2RZQyiHagnBkLt5hBT+g240/QDZZU\navrwM8Yo0HtEb8LyoP0mYV4O6jTFRgAAJXPJclNQOtgB+XG5XIf3SvGvL50kDMoY\nzBmszduL9SIKxALNTVOO+/WMMHl/CI3/bUbgmHr9DXynN8McrcNRn9EfkdKPNG4d\neBf1TyU3c/k/89iWmECoycKschzBPE1c9hp526R/5RMbxx2JzGuFuZO9laYeUFbX\nKnCSFX+mJqdIcBj7GJI+dh0kh2RS9Dbbe3460n0=\n-----END CERTIFICATE REQUEST-----\n'}
	== press <enter> to continue, <ctrl+c> to abort!

	=> sending request to API Gateway...
	<= headers: CaseInsensitiveDict({'x-amzn-requestid': '2548e86a-3e54-11e8-bf43-c750bb033a59', 'content-length': '1389', 'via': '1.1 008ae64ab7020a9aecc4c202669805d4.cloudfront.net (CloudFront)', 'x-cache': 'Miss from cloud front', 'x-amz-apigw-id': 'FOt0OGbzLPEFtQw=', 'x-amzn-trace-id': 'sampled=0;root=1-5acf5ce7-f0f1ad4f69bfe6aab1fe28de', 'connection': 'keep-alive', 'x-amz-cf-id': 'uOiG77A6Egn9R9voBea5pm40h2YquuVPEcThgegfJDS4oAUHumqg6A==', 'date': 'Thu, 12 Apr 2018 13:19:38 GMT', 'content-type': 'application/json'})
	<= text: {"status": "success", "distance": 472.3831871963406, "endpointAddress": "anb9aqgu7xd6q.iot.us-east-2.amazonaws.com", "certificatePem": "-----BEGIN CERTIFICATE-----\nMIIDUDCCAjigAwIBAgIVAJSUm9DDV90x8oJQtManP3iE0KrzMA0GCSqGSIb3DQEB\nCwUAME0xSzBJBgNVBAsMQkFtYXpvbiBXZWIgU2VydmljZXMgTz1BbWF6b24uY29t\nIEluYy4gTD1TZWF0dGxlIFNUPVdhc2hpbmd0b24gQz1VUzAeFw0xODA0MTIxMzE3\nMzdaFw00OTEyMzEyMzU5NTlaMBQxEjAQBgNVBAMMCW15ZGV2aWNlMzCCASIwDQYJ\nKoZIhvcNAQEBBQADggEPADCCAQoCggEBANRI5y05JS2aVWeISitTe8om18xgQIF0\ndl1+zvY/Tv3tmfDqOdS6Q/qxGzKKC4mZMcNunid+90AMya7qZNxFNYVUo5Vom1wb\nlrLTJvkZP07S7jQN0qJjCRecRL/a3TyWEPdwRuTHOx51q/28TK714mOHvZou99Kv\nZEHMaajgWhJtWkCiw3RrGDBZZTmUC5ddbUV7HrCkWHHI98KAQXXORnMy/P1/pjxE\nYPObCmYXfalOrZvuLk+7U4YLQasKb2sfzuAyMTabL2aPElpsoXHBjGNn2eJDPljp\nqrQSF6zjztV8WGZueFDjyG6K/Q90NFdzbe7f9/3Ybgbq5JgsFqmjyrkCAwEAAaNg\nMF4wHwYDVR0jBBgwFoAU3w0vC3+7YSqpHx0zBwPHp0n/G0IwHQYDVR0OBBYEFCcZ\nmGaIQDStdWmF9wILb4BlyXpQMAwGA1UdEwEB/wQCMAAwDgYDVR0PAQH/BAQDAgeA\nMA0GCSqGSIb3DQEBCwUAA4IBAQCbRnd2O/YhKJfRdZdKC9H4tZGTXf9XEdQR9hyv\nl0giigGigh3cBOQleuAIFjUyjta/LgHDO5PFC8F8H9QClBlV4Ja8YxKu37Jd0h8A\nfj0AmRvpoqA3lRUpbi/O+lNnGCjkBEWE1g/QpbnTmGVjb6IiE9aNMYLTk7SO1u/I\n8XIPwfKgl5jDZ+xjvnOmckBrI8GX0AjiYPw9tMsqWZt7WA37So5UYHRnYuoP1xZ7\n+jQ8feReDowpUDcXHIHn58oZTo9XUwuARltpYFiyRVrTzSPPtWDp1WfQzwDbxYgb\nY9nEnXkio0vb8UwrEdczMNBHAvqiIHvaE21Ey4chOi+qLujh\n-----END CERTIFICATE-----\n", "region": "us-east-2"}
	== press <enter> to continue, <ctrl+c> to abort!

	=> writing cert/key to file...
	=> device is ready to communicate with AWS IoT...
	== press <enter> to continue, <ctrl+c> to abort!

	<= device connected to AWS IoT in region: us-east-2
	 before you continue subscribe in the AWS IoT console to the topic: data/mydevice3/misc
	== press <enter> to continue, <ctrl+c> to abort!

	=> start publishing... press <ctrl+c> to abort
	=> publishing message: {'thing-name': 'mydevice3', 'global': 'device provisioning', 'date time': '2018-04-12T13:20:32'}
	=> publishing message: {'thing-name': 'mydevice3', 'global': 'device provisioning', 'date time': '2018-04-12T13:20:34'}



Lookup the provisioned device in the Dynamo Db table

As part of the setup of the global device provisioning solution a DynamoDB table named `iot-global-provisioning` has been created and you have populated it with information about the devices which should be provisioned. By getting the entry for `mydevice3` from the DynamoDB table you should find the time when the device was provisioned as well as the region in which the device has been created and the provisioning status (prov_status) is now set to `provisioned`.

Get item:

	aws dynamodb get-item --table-name iot-global-provisioning --key '{"thing_name": {"S": "mydevice3"}}'

The output should look similar to:

	{
	  "Item": {
	    "aws_region": {
	      "S": "us-east-2"
	    },
	    "prov_datetime": {
	      "S": "2018-05-15T10:47:12"
	    },
	    "thing_name": {
	      "S": "mydevice2"
	    },
	    "prov_status": {
	      "S": "provisioned"
	    }
	  }
	}

If you start the device again with the command `./global-device.py -t mydevice3 -a https://abcdefg.execute-api.AWS_REGION.amazonaws.com/test/device-provisioning -k` it will notice that it has already been provisioned because of the existing device key and device certificate and will immediately start publishing messages towards AWS IoT Core.


### Modes to run the global device
The global device can be run in three modes:

1. Send the thing name only in the provisioning request and receive private key, certificate and iot endpoint

		./global-device.py -t mydevice1 -a <YOUR_API_GATEWAY_URL>

2. Create a private key and send thing name and CSR in the provisioning request

		./global-device.py -t mydevice2 -a <YOUR_API_GATEWAY_URL> -k

3. Send a provisioning request with a wrong signature to demonstrate the failure of the signature verification process

		./global-device.py -t mydevice3 -a <YOUR_API_GATEWAY_URL> -f


### Outlook/Improvements

#### Best Region

As this is  an example implementation one can also think at various other scenarios how the best region for a device could be determined. You could define one AWS region per continent or a specific regions for particular countries e.g. if legal requirements exists.

#### Unique Key Pair per Device

In the sample implementation all devices share one private key to sign data in the provisioning request. The related public key is include in the Lambda installation package. An approach to use a unique key pair per device could be to deploy a unique private key on each device and to store the related public key in the DynamoDB table for device provisioning.

#### Securing [ipstack.com](http://ipstack.com/) Api Access Key in Environment Variable

If you want to secure sensitive information in environment variables like the [ipstack.com](http://ipstack.com/) API Access Key you can [encrypt your environment variables for lambda](https://docs.aws.amazon.com/lambda/latest/dg/env_variables.html#env_encrypt).

## License Summary

This sample code is made available under a modified MIT license. See the LICENSE file.