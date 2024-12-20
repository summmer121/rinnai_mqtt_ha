import json
import logging
from typing import Dict, Any, List
import utils.constants as const


class DeviceDataObserver:
    def update(self, device_data: Dict[str, Any]) -> None:
        pass


class MessageProcessor:
    def __init__(self):
        self.device_data = {
            "state": {},
            "gas": {},
            "supplyTime": {}
        }
        self.observers: List[DeviceDataObserver] = []

    def register_observer(self, observer: DeviceDataObserver) -> None:
        self.observers.append(observer)

    def notify_observers(self) -> None:
        for observer in self.observers:
            observer.update(self.device_data)

    def _process_hex_value(self, value: str, param_name: str) -> str:
        """Convert hex value to decimal string."""
        try:
            return str(int(value, 16))
        except ValueError as e:
            logging.warning(f"Invalid hex value for {param_name}: {value}")
            raise ValueError(
                f"Invalid hex value for {param_name}: {value}") from e

    def _get_operation_mode(self, mode_code: str) -> str:
        mode_mapping = const.OPERATION_MODES
        return mode_mapping.get(mode_code, f"invalid ({mode_code})")

    def _get_burning_state(self, state_code: str) -> str:
        state_mapping = const.BURNING_STATES
        return state_mapping.get(state_code, f"invalid ({state_code})")

    def _process_device_info(self, parsed_data: Dict[str, Any]) -> None:
        """Process device information from parsed message."""
        state_mapping = {
            'operationMode': self._get_operation_mode,
            'roomTempControl': lambda x: self._process_hex_value(x, 'roomTempControl'),
            'heatingOutWaterTempControl': lambda x: self._process_hex_value(x, 'heatingOutWaterTempControl'),
            'burningState': self._get_burning_state,
            'hotWaterTempSetting': lambda x: self._process_hex_value(x, 'hotWaterTempSetting'),
            'heatingTempSettingNM': lambda x: self._process_hex_value(x, 'heatingTempSettingNM'),
            'heatingTempSettingHES': lambda x: self._process_hex_value(x, 'heatingTempSettingHES')
        }

        for param in parsed_data.get('enl', []):
            try:
                param_id = param.get('id')
                param_data = param.get('data')

                if not param_id or not param_data:
                    continue

                if param_id in state_mapping:
                    self.device_data["state"][param_id] = state_mapping[param_id](
                        param_data)

            except Exception as e:
                logging.error(f"Error processing parameter {param_id}: {e}")

    def _process_energy_data(self, parsed_data: Dict[str, Any]) -> None:
        """Process energy consumption data."""
        time_parameters = const.TIME_PARAMETERS

        for param in parsed_data.get('egy', []):
            if not isinstance(param, dict):
                logging.warning(f"Skipping invalid parameter entry: {param}")
                continue

            # Process gas consumption
            if gas_value := param.get('gasConsumption'):
                try:
                    self.device_data["gas"]["gasConsumption"] = self._process_hex_value(
                        gas_value, 'gasConsumption')
                except ValueError:
                    continue

            # Process time-related parameters
            for key in param.keys() & time_parameters:
                try:
                    self.device_data["supplyTime"][key] = self._process_hex_value(
                        param[key], key)
                except ValueError:
                    logging.warning(f"Failed to process {key}")
                    continue

    def process_message(self, msg):
        """Process incoming Rinnai device messages."""
        try:
            parsed_data = json.loads(msg.payload.decode('utf-8'))
            parsed_topic = msg.topic.split('/')[-2]

            if not parsed_data or not parsed_topic:
                logging.warning("Received invalid or empty message")
                return

            if (parsed_topic == 'inf' and
                parsed_data.get('enl') and
                    parsed_data.get('code') == "FFFF"):
                self._process_device_info(parsed_data)
                self.notify_observers()  # Notify observers after processing device info

            elif (parsed_topic == 'stg' and
                    parsed_data.get('egy') and
                    parsed_data.get('ptn') == "J05"):
                self._process_energy_data(parsed_data)
                self.notify_observers()  # Notify observers after processing energy data

        except json.JSONDecodeError:
            logging.error("Failed to parse JSON message")
        except Exception as e:
            logging.error(f"Unexpected error in message processing: {e}")
