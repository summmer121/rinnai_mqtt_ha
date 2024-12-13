# rinnai_mqtt
抛砖引玉，该项目仅试了`RBS-**G56系列`该设备，设备id为`0F06000C`，其他设备和对应mqtt主题需要根据设备自行抓包添加
```
"productName": "采暖炉",
"productType": 0,
"classID": "0F06000C",
"classIDName": "RBS-**G56系列",
"classIDShow": "G56"
```
## update
- 解包了林内智家apk,对一些模式描述进行了优化，`RBS-**G56`系列应该可以免抓包直接使用用户名+密码使用了
- 中转林内智家mqtt通知到HA,实现可以在HA查看锅炉状态和调整温度，获取锅炉耗气量，其他功能可以自行修改
```
- RINNAI_USERNAME=yourphone
- RINNAI_PASSWORD=yourpassword
- LOCAL_MQTT_HOST=yourhamqtt
```


## docker run 
```
docker run -d \
  --name rinnai_mqtt_ha \
  -e RINNAI_USERNAME=user \
  -e RINNAI_PASSWORD=pass \
  -e LOCAL_MQTT_HOST=localhost 
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
      RINNAI_USERNAME: user
      RINNAI_PASSWORD: pass
      LOCAL_MQTT_HOST: localhost  # 本地mqtt地址
```
# 效果展示
HA中MQTT可以自行发现
![image](https://github.com/user-attachments/assets/4ec03ab1-56ab-4574-9f59-13eea7ad464c)


