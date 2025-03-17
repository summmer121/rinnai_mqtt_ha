import ssl
import json
import logging
from .mqtt_client import MQTTClientBase
from processors.message_processor import MessageProcessor


class RinnaiClient(MQTTClientBase):
    def __init__(self, config, message_processor: MessageProcessor):
        super().__init__(f"{config.RINNAI_USERNAME}")
        self.config = config
        self.message_processor = message_processor
        self.topics = config.get_rinnai_topics()
        self.connected = False
        self.update_timer = None
        self.disconnect_timer = None
        logging.info(f"Rinnai topics: {self.topics}")

        # Configure TLS
        self.client.tls_set(
            cert_reqs=ssl.CERT_NONE,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        self.client.tls_insecure_set(True)
        self.client.username_pw_set(
            self.config.RINNAI_USERNAME, self.config.RINNAI_PASSWORD)

    def schedule_update(self):
        """定时更新任务"""
        self.connect_and_update()
        self.update_timer = threading.Timer(
            self.config.RINNAI_UPDATE_INTERVAL, self.schedule_update)
        self.update_timer.start()

    def connect_and_update(self):
        """连接并获取更新"""
        if not self.connected:
            self.connect(self.config.RINNAI_HOST, self.config.RINNAI_PORT)
            self.connected = True
            # 设置断开连接定时器
            if self.disconnect_timer:
                self.disconnect_timer.cancel()
            self.disconnect_timer = threading.Timer(
                self.config.RINNAI_CONNECT_TIMEOUT, self.disconnect_and_cleanup)
            self.disconnect_timer.start()

    def disconnect_and_cleanup(self):
        """断开连接并清理"""
        if self.connected:
            self.disconnect()
            self.connected = False

    def send_command(self, topic, payload):
        """发送命令时临时连接"""
        self.connect_and_update()
        self.publish(topic, payload)

    def stop(self):
        """停止所有定时器"""
        if self.update_timer:
            self.update_timer.cancel()
        if self.disconnect_timer:
            self.disconnect_timer.cancel()
        self.disconnect_and_cleanup()
    
    def on_connect(self, client, userdata, flags, rc):
        logging.info(f"Rinnai MQTT connect status: {rc}")
        if rc == 0:
            for topic in self.topics.values():
                self.subscribe(topic)
        
        # self.set_default_status()
        


    def on_message(self, client, userdata, msg):
        try:
            logging.info(
                f"Rinnai msg topic: {msg.topic}, payload: {json.loads(msg.payload.decode('utf-8'))}")
            self.message_processor.process_message(msg)
        except Exception as e:
            logging.error(f"Rinnai message error: {e}")

    def set_temperature(self, heat_type, temperature):
        if not heat_type:
            raise ValueError("Error: heat type not specified")

        request_payload = {
            "code": self.config.AUTH_CODE,
            "enl": [
                {
                    "data": hex(temperature)[2:].upper().zfill(2),
                    "id": heat_type
                }
            ],
            "id": self.config.DEVICE_TYPE,
            "ptn": "J00",
            "sum": "1"
        }
        self.publish(self.topics["set"], json.dumps(request_payload), qos=1)
        logging.info(f"Set {heat_type} temperature to {temperature}°C")

    def set_mode(self, mode):
        if not mode:
            raise ValueError("Error: mode not specified")

        request_payload = {
            "code": self.config.AUTH_CODE,
            "enl": [
                {
                    "data": "31",
                    "id": mode
                }
            ],
            "id": self.config.DEVICE_TYPE,
            "ptn": "J00",
            "sum": "1"
        }
        self.publish(self.topics["set"], json.dumps(request_payload), qos=1)
        logging.info(f"Set mode to: {mode}")

    def set_default_status(self):
        default_status = {'enl': []}
        for key, value in self.config.INIT_STATUS.items():
            default_status['enl'].append({'id': key, 'data': value})
        self.message_processor._process_device_info(default_status)
        self.message_processor.notify_observers()
