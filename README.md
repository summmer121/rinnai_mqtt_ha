# rinnai_mqtt
抛砖引玉，该项目仅试了`RBS-**G56系列`该设备，设备id为`0F06000C`，其他设备和对应mqtt主题需要根据设备自行抓包添加
```
"productName": "采暖炉",
"productType": 0,
"classID": "0F06000C",
"classIDName": "RBS-**G56系列",
"classIDShow": "G56"
```
中转林内智家mqtt通知到HA,实现可以在HA查看锅炉状态和调整温度，其他功能可以自行修改
需要自己抓包获取信息配置，
- DEVICE_ID 为设备id，可抓包获取
- RINNAI_HOST 已知为 `mqtt.rinnai.com.cn`
- RINNAI_PORT 已知为 `8883`
- RINNAI_USERNAME 已知为 `a:rinnai:SR:01:SR:手机号`
- RINNAI_PASSWORD 需抓包  api/v1/login
- DEVICE_SN 已知为 设备对应的mac地址

## docker run 
```
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
```

## docker-compose
```
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
```
HA中MQTT可以自行发现
![image](https://github.com/user-attachments/assets/ac388675-535c-4908-aeb8-4aefaa4a204a)
