#!/bin/sh
cd /userdata
wget -q -O camevision_agent.py http://192.168.1.44:18765/camevision_agent.py
sed -i 's/\r$//' camevision_agent.py
echo PUT_AGENT
