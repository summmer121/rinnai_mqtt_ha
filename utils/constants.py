# MQTT Topics
TOPIC_TYPES = {
    "DEVICE_INFO": "inf",
    "ENERGY_DATA": "stg",
    "DEVICE_CONTROL": "set"
}

# Device States
OPERATION_MODES = {
    "0": "关机",
    "1": "采暖关闭",
    "2": "休眠",
    "3": "冬季普通",
    "4": "快速热水",
    "B": "采暖节能",
    "23": "采暖预约",
    "13": "采暖外出",
    "43": "快速采暖",
    "4B": "快速采暖/节能",
    "53": "快速采暖/外出",
    "63": "快速采暖/预约"
}

BURNING_STATES = {
    "30": "待机中",
    "31": "烧水中",
    "32": "燃烧中",
    "33": "异常"
}

# Message Types
TIME_PARAMETERS = {
    'totalPowerSupplyTime',
    'actualUseTime',
    'totalHeatingBurningTime',
    'burningtotalHotWaterBurningTimeState',
    'heatingBurningTimes',
    'hotWaterBurningTimes'
}

STATE_PARAMETERS = {
    'operationMode',
    'roomTempControl',
    'heatingOutWaterTempControl',
    'burningState',
    'hotWaterTempSetting',
    'heatingTempSettingNM',
    'heatingTempSettingHES'
}


HOST = "https://iot.rinnai.com.cn/app"
LOGIN_URL = f"{HOST}/V1/login"
INFO_URL = f"{HOST}/V1/device/list"
PROCESS_PARAMETER_URL = f"{HOST}/V1/device/processParameter"
# 林内智家app内置accessKey
AK = "A39C66706B83CCF0C0EE3CB23A39454D" 