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
- 更新支持本地mqtt可以配置密码连接
```
- RINNAI_USERNAME=yourphone
- RINNAI_PASSWORD=yourpassword
- LOCAL_MQTT_HOST=yourhamqtt
- LOCAL_MQTT_POST=yourhamqttport
- LOCAL_MQTT_USERNAME=test
- LOCAL_MQTT_PASSWORD=test
- LOCAL_MQTT_TLS=Fasle # 本地mqtt地址如果是https需要开启，默认不开启
- LOGGING=True #是否开启日志
```

## 配合bubble-card展示UI基本可以替换app

![image](https://github.com/user-attachments/assets/e8f034cf-0783-4833-b444-9466b4e1b76f)

- 统计每日燃气消耗配置（）
```yaml

utility_meter:
  daily_gas_consumption:
    source: sensor.rinnai_heater_rinnai_hao_qi_liang 
    cycle: daily
    offset:
      hours: 0
      minutes: 0

template:
  - sensor:
      - name: "Daily Gas Usage Calibrated"
        unique_id: daily_gas_usage_calibrated
        unit_of_measurement: "m³"
        state: >
          {% set current_meter = states('sensor.daily_gas_consumption') | float(0) %}
          {% set last_reset = state_attr('sensor.daily_gas_consumption', 'last_reset') %}
          {% set start_time = as_timestamp(last_reset) if last_reset else 0 %}
          {% set now = as_timestamp(now()) %}
          {% set hours_since_reset = ((now - start_time) / 3600) | float(0) %}
          
          {% if hours_since_reset <= 24 %}
            {% if hours_since_reset > 0 %}
              {{ current_meter }}
            {% else %}
              {{ 0 }}
            {% endif %}
          {% else %}
            {{ state | float(0) }}
          {% endif %}
        attributes:
          last_reset: >
            {{ state_attr('sensor.daily_gas_consumption', 'last_reset') }}
          time_since_reset_hours: >
            {% set last_reset = state_attr('sensor.daily_gas_consumption', 'last_reset') %}
            {% set start_time = as_timestamp(last_reset) if last_reset else 0 %}
            {% set now = as_timestamp(now()) %}
            {{ ((now - start_time) / 3600) | round(2) }}
          data_quality: >
            {% set last_reset = state_attr('sensor.daily_gas_consumption', 'last_reset') %}
            {% set start_time = as_timestamp(last_reset) if last_reset else 0 %}
            {% set now = as_timestamp(now()) %}
            {% set hours_since_reset = ((now - start_time) / 3600) | float(0) %}
            {% if hours_since_reset <= 24 %}
              {% if hours_since_reset > 0 %}
                {{ "good" }}
              {% else %}
                {{ "initializing" }}
              {% endif %}
            {% else %}
              {{ "stale" }}
            {% endif %}
```



## docker run 
```
docker run -d \
  --restart always \
  -e RINNAI_USERNAME=yourphone \
  -e RINNAI_PASSWORD=yourpassword \
  -e LOCAL_MQTT_HOST=yourhamqtt \
  -e LOCAL_MQTT_POST=yourhamqttport \
  -e LOCAL_MQTT_USERNAME=test \
  -e LOCAL_MQTT_PASSWORD=test \
  -e LOCAL_MQTT_TLS=False \
  -e LOGGING=True \
  ghcr.io/palafin02back/rinnai_mqtt_ha:release
```

## docker-compose
```
version: "3.8"
services:
  rinnai_mqtt:
    image: ghcr.io/palafin02back/rinnai_mqtt_ha:release
    restart: always
    environment:
      - RINNAI_USERNAME=yourphone
      - RINNAI_PASSWORD=yourpassword
      - LOCAL_MQTT_HOST=yourhamqtt
      - LOCAL_MQTT_POST=yourhamqttport
      - LOCAL_MQTT_USERNAME=test
      - LOCAL_MQTT_PASSWORD=test
      - LOCAL_MQTT_TLS=False
      - LOGGING=True
```
# 效果展示
HA中MQTT可以自行发现
![image](https://github.com/user-attachments/assets/19b55ddf-fae5-4025-b769-557bce473124)



