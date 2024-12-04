# 使用官方的 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制当前目录的内容到工作目录
COPY . /app

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量（根据需要修改）
ENV DEVICE_ID=0F06000C \
    MQTT_HOST=localhost \
    MQTT_PORT=1883 \
    RINNAI_HOST=localhost \
    RINNAI_PORT=8883 \
    RINNAI_USERNAME=user \
    RINNAI_PASSWORD=pass \
    LOCAL_MQTT_HOST=localhost \
    LOCAL_MQTT_PORT=1883

# 赋予启动脚本执行权限
RUN chmod +x start.sh

# 运行启动脚本
CMD ["./start.sh"]