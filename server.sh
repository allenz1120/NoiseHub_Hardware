#!/bin/bash

screen -d -m python3 pubsub_noise.py --topic topic_1 --root-ca ~/NoiseHub_Hardware/certs/AmazonRootCA1.pem --cert ~/NoiseHub_Hardware/certs/e7fa0e57e5f0499d6cde1b499f9207811c6224186b5ebc3abbba1f9fd145c08f-certificate.pem.crt --key ~/NoiseHub_Hardware/certs/e7fa0e57e5f0499d6cde1b499f9207811c6224186b5ebc3abbba1f9fd145c08f-private.pem.key --endpoint a2df4033s7h9cp-ats.iot.us-east-2.amazonaws.com
