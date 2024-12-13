#!/bin/sh


python rinnai_http_proxy.py

python rinnai_mqtt_discovery.py

python rinnai_mqtt_ha.py