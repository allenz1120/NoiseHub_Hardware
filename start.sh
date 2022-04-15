#!/bin/bash

sudo apt-get install -y libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0

sudo apt-get install -y ffmpeg libav-tools

sudo apt-get install -y python3-pip

pip install -r requirements.txt

cd aws-sdk/samples

screen -d -m python3 noise_client.py
