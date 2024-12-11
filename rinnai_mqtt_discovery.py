import paho.mqtt.client as mqtt
import json
import uuid
import os
class RinnaiHomeAssistantDiscovery:
    def __init__(self):
        self.mqtt_host = os.getenv('LOCAL_MQTT_HOST')
        self.mqtt_port = int(os.getenv('LOCAL_MQTT_PORT', '1883'))
        self.device_sn = os.getenv('DEVICE_SN')
        # 唯一标识符
        self.unique_id = f"rinnai_{self.device_sn}"
        # MQTT客户端
        self.client = mqtt.Client(
            client_id=f"ha_discovery_{str(uuid.uuid4())[:8]}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
        self.client.on_connect = self.on_connect
        # Home Assistant Discovery主题
        self.discovery_prefix = "homeassistant"

    def on_connect(self, client, userdata, flags, rc):
        print(f"连接Home Assistant MQTT: {rc}")

    def generate_config(self, component_type, object_id, name, topic, config_type='sensor', unit=None):
        """
        生成通用配置
        """
        base_topic = f"{self.discovery_prefix}/{component_type}/rinnai_{self.device_sn}_{object_id}"

        config = {
            "name": name,
            "unique_id": f"{self.unique_id}_{object_id}",
            "state_topic": f"local_mqtt/{self.device_sn}/state",
            "value_template": f"{{{{ value_json.{object_id} }}}}",
            "device": {
                "identifiers": [self.unique_id],
                "name": "Rinnai Water Heater",
                "manufacturer": "Rinnai",
                "model": "Smart Water Heater"
            }
        }

        # 添加单位
        if unit:
            config["unit_of_measurement"] = unit

        if config_type == 'number':
            config.update({
                "command_topic": topic,
                "min": 35,
                "max": 80,
                "step": 1,
                "unit_of_measurement": "°C"
            })

        return f"{base_topic}/config", json.dumps(config)

    def publish_discovery_configs(self):
        """
        发布Home Assistant自动发现配置
        """
        self.client.connect(self.mqtt_host, self.mqtt_port, 60)

        # 传感器配置
        sensors = [
            ("操作模式", "operationMode", None),
            ("室温控制", "roomTempControl", "°C"),
            ("加热出水温度控制", "heatingOutWaterTempControl", "°C"),
            ("燃烧状态", "burningState", None),
            ("热水温度设置", "hotWaterTempSetting", "°C"),
            ("普通模式加热温度", "heatingTempSettingNM", "°C"),
            ("HES模式加热温度", "heatingTempSettingHES", "°C")
        ]

        for label, object_id, unit in sensors:
            topic, config = self.generate_config(
                'sensor',
                object_id,
                f"Rinnai {label}",
                None,
                'sensor',
                unit
            )
            self.client.publish(topic, config, retain=True)

        # 温度控制器配置
        temp_controls = [
            ("热水温度", "hotWaterTempSetting",f"local_mqtt/{self.device_sn}/set/hot_water_temp"),
            ("地暖温度", "heatingTempSettingNM",f"local_mqtt/{self.device_sn}/set/heating_temp_nm")
        ]

        for label, object_id, topic in temp_controls:
            number_topic, number_config = self.generate_config(
                'number',
                object_id,
                f"Rinnai {label}",
                topic,
                'number'
            )
            self.client.publish(number_topic, number_config, retain=True)

        self.client.disconnect()


def main():
    discovery = RinnaiHomeAssistantDiscovery()
    discovery.publish_discovery_configs()


if __name__ == "__main__":
    main()
