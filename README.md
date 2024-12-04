# rinnai_mqtt
hook rinnai mqtt msg


docker run 
'''
docker run -d \
  --name rinnai_mqtt_ha \
  -e DEVICE_ID=000000 \
  -e RINNAI_HOST=localhost \
  -e RINNAI_PORT=8883 \
  -e RINNAI_USERNAME=user \
  -e RINNAI_PASSWORD=pass \
  -e LOCAL_MQTT_HOST=localhost \
  -e LOCAL_MQTT_PORT=1883 \
  ghcr.io/palafin02back/rinnai_mqtt_ha:release

'''

docker-compose
'''
version: '3.8'
services:
  rinnai_mqtt_ha:
    image: ghcr.io/palafin02back/rinnai_mqtt_ha:release
    container_name: rinnai_mqtt_ha
    environment:
      DEVICE_ID: 000000    # 设备id
      RINNAI_HOST: localhost  
      RINNAI_PORT: 8883
      RINNAI_USERNAME: user
      RINNAI_PASSWORD: pass
      LOCAL_MQTT_HOST: localhost  # 本地mqtt地址
      LOCAL_MQTT_PORT: 1883

'''
