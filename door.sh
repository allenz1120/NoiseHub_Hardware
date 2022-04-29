#!/bin/bash

sudo apt install screen

cd aws-sdk/samples

screen -d -m python3 pubsub_door.py --topic topic_2 --root-ca ~/NoiseHub_Hardware/certs/AmazonRootCA1.pem --cert ~/NoiseHub_Hardware/certs/a90dd13027cbad9fbdeef437be031fbca86e052e04fb77597a8e853c5cea33a7-certificate.pem.crt --key ~/NoiseHub_Hardware/certs/a90dd13027cbad9fbdeef437be031fbca86e052e04fb77597a8e853c5cea33a7-private.pem.key --endpoint a2df4033s7h9cp-ats.iot.us-east-2.amazonaws.com
