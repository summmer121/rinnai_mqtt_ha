import logging
from config import Config
from clients.rinnai_client import RinnaiClient
from clients.local_client import LocalClient
from clients.http_client import RinnaiHttpClient
from clients.ha_discovery_client import RinnaiHomeAssistantDiscovery
from processors.message_processor import MessageProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    try:
        # Initialize configuration
        config = Config()
        logger.disabled = config.LOGGING == 'true'
        # Create message processor
        message_processor = MessageProcessor()

        # Initialize clients
        rinnai_client = RinnaiClient(config, message_processor)
        local_client = LocalClient(config, rinnai_client)
        rinnai_http_client = RinnaiHttpClient(config)
        rinnai_ha_discovery = RinnaiHomeAssistantDiscovery(config)

        if not rinnai_http_client.init_data():
            logger.error("Failed to initialize Rinnai HTTP client data.")
            return
        # Publish Home Assistant discovery configurations
        rinnai_ha_discovery.publish_discovery_configs()
        # Connect to MQTT brokers
        rinnai_client.connect(config.RINNAI_HOST, config.RINNAI_PORT)
        local_client.connect(config.LOCAL_MQTT_HOST, config.LOCAL_MQTT_PORT)

        # Start clients
        rinnai_client.start()

        # Local client runs in main thread
        logger.info("Starting rinnai mqtt integration...")
        local_client.client.loop_forever()

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        rinnai_client.stop()
        local_client.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
