import requests
import os
import hashlib
import logging
import utils.constants as const


class RinnaiHttpClient:
    def __init__(self, config):
        self.config = config
        self.token = None
        self.device_info = {
            "mac": None,
            "name": None,
            "authCode": None,
            "deviceType": None,
            "deviceId": None
        }

    def login(self):
        params = {
            "username": self.config.RINNAI_HTTP_USERNAME,
            "password": self.config.RINNAI_PASSWORD,
            "accessKey": const.AK,
            "appType": "2",
            "appVersion": "3.1.0",
            "identityLevel": "0"
        }
        logging.info(f"Logging in with params: {params}")
        response = requests.get(const.LOGIN_URL, params=params)
        if response.status_code == 200 and response.json().get("success") != False:
            self.token = response.json().get("data").get("token")
            logging.info(f"Login success, token: {self.token}")
            return True
        logging.error("Login failed")
        return False

    def get_devices(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(const.INFO_URL, headers=headers)
        if response.status_code == 200 and response.json().get("success"):
            devices = response.json().get("data").get("list")
            logging.info(f"Devices: {devices}")
            if devices and devices[0].get("online") == "1":
                self.device_info = {
                    "mac": devices[0].get("mac"),
                    "name": devices[0].get("name"),
                    "authCode": devices[0].get("authCode"),
                    "deviceType": devices[0].get("deviceType"),
                    "deviceId": devices[0].get("id")
                }
                return self.device_info
        logging.error("No devices found or device is offline")
        return None

    def get_device_info(self):
        return self.device_info

    def init_data(self):
        if self.login():
            device_info = self.get_devices()
            if device_info:
                return True
        return False

# def main():
#     rinnai_client = RinnaiClient(
#         os.getenv('RINNAI_USERNAME'), os.getenv('RINNAI_PASSWORD'))
#     if rinnai_client.login():
#         device_info = rinnai_client.get_devices()
#         if device_info:
#             logger.info(
#                 f"Current device info: {rinnai_client.get_device_info()}")
#         else:
#             logger.error("Failed to retrieve device information.")
#     else:
#         logger.error("Login failed.")


# if __name__ == "__main__":
#     main()
