import paho.mqtt.client as mqtt
import json
import ssl
import uuid
import time
import os


class RinnaiHomeAssistantIntegration:
    def __init__(self, rinnai_host, rinnai_port, rinnai_username, rinnai_password,device_sn, local_mqtt_host, local_mqtt_port):
        # Rinnai原始配置
        self.rinnai_host = os.getenv('RINNAI_HOST', rinnai_host)
        self.rinnai_port = os.getenv('RINNAI_PORT', rinnai_port)
        self.rinnai_username = os.getenv('RINNAI_USERNAME', rinnai_username)
        self.rinnai_password = os.getenv('RINNAI_PASSWORD', rinnai_password)
        self.device_sn = os.getenv('DEVICE_SN', device_sn)

        # 本地MQTT服务器配置
        self.local_mqtt_host = os.getenv('LOCAL_MQTT_HOST', local_mqtt_host)
        self.local_mqtt_port = os.getenv('LOCAL_MQTT_PORT', local_mqtt_port)

        # Rinnai MQTT客户端
        self.rinnai_client = self._create_rinnai_client()

        # 本地MQTT客户端
        self.local_client = self._create_local_client()

        # 状态存储
        self.device_state = {}

    def _create_rinnai_client(self):
        client = mqtt.Client(
            client_id=f"rinnai_ha_bridge_{str(uuid.uuid4())[:8]}",
            transport="tcp",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
        client.tls_set(
            cert_reqs=ssl.CERT_NONE,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        client.tls_insecure_set(True)
        client.username_pw_set(self.rinnai_username, self.rinnai_password)
        client.on_connect = self.on_rinnai_connect
        client.on_message = self.on_rinnai_message
        return client

    def _create_local_client(self):
        client = mqtt.Client(
            client_id=f"rinnai_ha_local_{str(uuid.uuid4())[:8]}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
        client.on_connect = self.on_local_connect
        client.on_message = self.on_local_message
        return client

    def on_rinnai_connect(self, client, userdata, flags, rc):
        print(f"连接Rinnai MQTT服务器状态: {rc}")
        if rc == 0:
            state_topic = f"rinnai/SR/01/SR/{self.device_sn}/inf/"
            client.subscribe(state_topic)

    def on_local_connect(self, client, userdata, flags, rc):
        print(f"连接本地MQTT服务器状态: {rc}")
        if rc == 0:
            # 订阅不同温度设置主题
            client.subscribe(
                f"rinnai/SR/01/SR/{self.device_sn}/set/hot_water_temp")
            client.subscribe(
                f"rinnai/SR/01/SR/{self.device_sn}/set/heating_temp_nm")

    def on_rinnai_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            parsed_data = json.loads(payload)
            print(f"收到Rinnai消息: {parsed_data}")
            # 提取所有状态信息
            if "enl" in parsed_data:
                # 重置设备状态
                self.device_state = {}

                for param in parsed_data['enl']:
                    param_id = param['id']
                    param_data = param['data']

                    # 根据参数ID映射到具体状态
                    if param_id == 'operationMode':
                        self.device_state['operationMode'] = self._get_operation_mode(
                            param_data)
                    elif param_id == 'roomTempControl':
                        self.device_state['roomTempControl'] = f"{int(param_data, 16)}"
                    elif param_id == 'heatingOutWaterTempControl':
                        self.device_state['heatingOutWaterTempControl'] = f"{int(param_data, 16)}"
                    elif param_id == 'burningState':
                        self.device_state['burningState'] = self._get_burning_state(
                            param_data)
                    elif param_id == 'hotWaterTempSetting':
                        self.device_state['hotWaterTempSetting'] = f"{int(param_data, 16)}"
                    elif param_id == 'heatingTempSettingNM':
                        self.device_state['heatingTempSettingNM'] = f"{int(param_data, 16)}"
                    elif param_id == 'heatingTempSettingHES':
                        self.device_state['heatingTempSettingHES'] = f"{int(param_data, 16)}"

                # 发布完整状态到本地MQTT
                self._publish_device_state()
        except Exception as e:
            print(f"解析Rinnai消息错误: {e}")

    def _publish_device_state(self):
        """
        发布完整的设备状态到本地MQTT
        """
        state_topic = f"rinnai/SR/01/SR/{self.device_sn}/state"
        self.local_client.publish(
            state_topic,
            json.dumps(self.device_state, ensure_ascii=False)
        )
        print(f"发布设备状态: {self.device_state}")

    def on_local_message(self, client, userdata, msg):
        # 处理来自Home Assistant的温度设置请求
        try:
            temperature = int(msg.payload.decode())

            # 根据主题设置不同的温度
            if msg.topic.endswith('hot_water_temp'):
                self.set_rinnai_temperature('hot_water', temperature)
            elif msg.topic.endswith('heating_temp_nm'):
                self.set_rinnai_temperature('heating', temperature)
        except Exception as e:
            print(f"处理本地温度设置错误: {e}")

    def set_rinnai_temperature(self, heat_type, temperature):
        # 根据热水类型构建不同的请求
        if heat_type == 'hot_water':
            param_id = 'hotWaterTempSetting'
        elif heat_type == 'heating':
            param_id = 'heatingTempSettingNM'
        else:
            raise ValueError("无效的热水类型")

        # 构建Rinnai温度设置消息
        request_payload = {
            "code": "03E9",
            "enl": [
                {
                    "data": hex(temperature)[2:].upper().zfill(2),
                    "id": param_id
                }
            ],
            "id": os.getenv('DEVICE_ID', '0F06000C'),
            "ptn": "J00",
            "sum": "1"
        }

        set_topic = f"rinnai/SR/01/SR/{self.device_sn}/set/"
        self.rinnai_client.publish(
            set_topic, json.dumps(request_payload), qos=1)
        print(f"设置{heat_type}温度为 {temperature}°C")

    def _get_operation_mode(self, mode_code):
        """转换操作模式编码"""
        mode_mapping = {
            "0": "待机",
            "1": "预热",
            "2": "制热",
            "3": "普通模式"
        }
        return mode_mapping.get(mode_code, f"未知模式({mode_code})")

    def _get_burning_state(self, state_code):
        """转换燃烧状态"""
        state_mapping = {
            "00": "关闭",
            "30": "预热中",
            "31": "点火中",
            "32": "燃烧中",
            "33": "异常"
        }
        return state_mapping.get(state_code, f"未知状态({state_code})")

    def start(self):
        # 连接Rinnai MQTT服务器
        self.rinnai_client.connect(
            self.rinnai_host,
            self.rinnai_port,
            60
        )

        # 连接本地MQTT服务器
        self.local_client.connect(
            self.local_mqtt_host,
            self.local_mqtt_port,
            60
        )

        # 启动客户端循环
        self.rinnai_client.loop_start()
        self.local_client.loop_forever()


def main():

    integration = RinnaiHomeAssistantIntegration()
    integration.start()


if __name__ == "__main__":
    main()
