import paho.mqtt.client as mqtt
import json
import ssl
import uuid
import time
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()
class RinnaiHomeAssistantIntegration:
    def __init__(self):
        # Rinnai原始配置
        password = os.getenv('RINNAI_PASSWORD')
        print(f"RINNAI_PASSWORD: {password}")
        self.rinnai_host = os.getenv('RINNAI_HOST', 'mqtt.rinnai.com.cn')
        self.rinnai_port = int(os.getenv('RINNAI_PORT', '8883'))
        self.rinnai_username = f"a:rinnai:SR:01:SR:{os.getenv('RINNAI_USERNAME')}"
        self.rinnai_password = str.upper(
            hashlib.md5(password.encode('utf-8')).hexdigest())
        self.device_sn = os.getenv('DEVICE_SN')

        # 本地MQTT服务器配置
        self.local_mqtt_host = os.getenv('LOCAL_MQTT_HOST')
        self.local_mqtt_port = int(os.getenv('LOCAL_MQTT_PORT', '1883'))

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
            """
            已知主题:
            rinnai/SR/01/SR/{device_sn}/sys/
            rinnai/SR/01/SR/{device_sn}/inf/
            rinnai/SR/01/SR/{device_sn}/set/
            rinnai/SR/01/SR/{device_sn}/res/
            rinnai/SR/01/SR/{device_sn}/get/
            rinnai/SR/01/SR/{device_sn}/stg/

            """
            state_topic = f"rinnai/SR/01/SR/{self.device_sn}/#"
            client.subscribe(state_topic)

    def on_local_connect(self, client, userdata, flags, rc):
        print(f"连接本地MQTT服务器状态: {rc}")
        if rc == 0:
            # 本地服务器订阅设置主题，区分热水和暖气
            client.subscribe(
                f"local_mqtt/{self.device_sn}/set/hot_water_temp")
            client.subscribe(
                f"local_mqtt/{self.device_sn}/set/heating_temp_nm")

    def on_rinnai_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            parsed_data = json.loads(payload)
            print(f"Rinnai Mqtt: {parsed_data}")
            self._process_rinnai_message(msg)
        except Exception as e:
            print(f"解析Rinnai消息错误: {e}")

    def _publish_device_state(self):

        # 发布完整的设备状态到本地MQTT
        state_topic = f"local_mqtt/{self.device_sn}/state"
        self.local_client.publish(
            state_topic,
            json.dumps(self.device_state, ensure_ascii=False)
        )
        print(f"Publish to local mqtt: {self.device_state}")

    def on_local_message(self, client, userdata, msg):
        try:
            temperature = int(msg.payload.decode())

            # 分别处理热水和暖气温度设置
            if msg.topic.endswith('hot_water_temp'):
                self.set_rinnai_temperature('hot_water', temperature)
            elif msg.topic.endswith('heating_temp_nm'):
                self.set_rinnai_temperature('heating', temperature)
        except Exception as e:
            print(f"local mqtt set fail: {e}")

    def set_rinnai_temperature(self, heat_type, temperature):

        if heat_type == 'hot_water':
            param_id = 'hotWaterTempSetting'
        elif heat_type == 'heating':
            param_id = 'heatingTempSettingNM'
        else:
            raise ValueError("error heat type")

        # 向林内服务器发布设置温度主题
        request_payload = {
            "code": os.getenv('AUTH_CODE'),
            "enl": [
                {
                    "data": hex(temperature)[2:].upper().zfill(2),
                    "id": param_id
                }
            ],
            "id": os.getenv('DEVICE_TYPE'),
            "ptn": "J00",
            "sum": "1"
        }

        set_topic = f"rinnai/SR/01/SR/{self.device_sn}/set/"
        self.rinnai_client.publish(
            set_topic, json.dumps(request_payload), qos=1)
        print(f"设置{heat_type}温度为 {temperature}°C")

    def _get_operation_mode(self, mode_code):
        """模式映射"""
        mode_mapping = {
            "3": "普通模式"
            "13" "外出模式"
        }
        return mode_mapping.get(mode_code, f"invalid ({mode_code})")

    def _get_burning_state(self, state_code):
        """
        已知状态码:
        30: 待机中
        31: 热水点火
        32: 燃气点火
        """
        
        state_mapping = {
            "30": "待机中",
            "31": "点火中",
            "32": "燃烧中",
            "33": "异常"
        }
        return state_mapping.get(state_code, f"invalid ({state_code})")

    def _process_rinnai_message(self, msg):
        payload = msg.payload.decode('utf-8')
        parsed_data = json.loads(payload)
        print(f"Rinnai Mqtt: {parsed_data}")
        if msg.topic.endswith('/inf/'):
            if "enl" in parsed_data:
                self.device_state = {}
                for param in parsed_data['enl']:
                    param_id = param['id']
                    param_data = param['data']

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
                self._publish_device_state()

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
