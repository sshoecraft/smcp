"""MQTT client wrapper."""

import logging
import ssl
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


@dataclass
class MQTTConfig:
    """Configuration for MQTT client."""
    broker: str
    port: int = 1883
    username: str = ""
    password: str = ""
    client_id: str = ""
    use_tls: bool = False

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "MQTTConfig":
        """Create config from SMCP credentials."""
        broker = creds.get("MQTT_BROKER")
        if not broker:
            raise ValueError("MQTT_BROKER credential is required")

        return cls(
            broker=broker,
            port=int(creds.get("MQTT_PORT", "1883")),
            username=creds.get("MQTT_USER", ""),
            password=creds.get("MQTT_PASS", ""),
            client_id=creds.get("MQTT_CLIENT_ID", ""),
            use_tls=creds.get("MQTT_TLS", "").lower() == "true",
        )


@dataclass
class MQTTMessage:
    """Represents a received MQTT message."""
    topic: str
    payload: str
    retain: bool
    qos: int


class MQTTClient:
    """MQTT client wrapper for MCP tools."""

    def __init__(self, config: MQTTConfig):
        """Initialize the MQTT client.

        Args:
            config: MQTTConfig instance with connection settings
        """
        self.config = config
        self.client_id = config.client_id or f"mcp-mqtt-{uuid.uuid4().hex[:8]}"

        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id
        )

        if config.username:
            self._client.username_pw_set(config.username, config.password)

        if config.use_tls:
            self._client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

        self._messages: Dict[str, List[MQTTMessage]] = {}
        self._lock = threading.Lock()
        self._connected = threading.Event()

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Handle connection callback."""
        if reason_code == 0:
            logger.info(f"Connected to MQTT broker {self.config.broker}:{self.config.port}")
            self._connected.set()
        else:
            logger.error(f"Failed to connect: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Handle disconnection callback."""
        logger.warning(f"Disconnected from MQTT broker: {reason_code}")
        self._connected.clear()

    def _on_message(self, client, userdata, msg):
        """Handle incoming message callback."""
        message = MQTTMessage(
            topic=msg.topic,
            payload=msg.payload.decode("utf-8", errors="replace"),
            retain=msg.retain,
            qos=msg.qos
        )

        with self._lock:
            if msg.topic not in self._messages:
                self._messages[msg.topic] = []
            self._messages[msg.topic].append(message)

        logger.debug(f"Received message on {msg.topic}: {message.payload[:100]}")

    def connect(self):
        """Connect to the MQTT broker."""
        logger.info(f"Connecting to {self.config.broker}:{self.config.port} as {self.client_id}")
        self._client.connect(self.config.broker, self.config.port, keepalive=60)
        self._client.loop_start()

        if not self._connected.wait(timeout=10):
            raise RuntimeError(f"Failed to connect to MQTT broker {self.config.broker}:{self.config.port}")

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("Disconnected from MQTT broker")

    async def publish(self, topic: str, message: str, retain: bool = False) -> Dict[str, Any]:
        """Publish a message to a topic.

        Args:
            topic: MQTT topic to publish to
            message: Message payload
            retain: Whether to retain the message

        Returns:
            Dict with success status
        """
        try:
            result = self._client.publish(topic, message, retain=retain)
            result.wait_for_publish(timeout=5)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published to {topic}: {message[:100]}")
                return {"topic": topic, "retain": str(retain)}
            else:
                return {"error": f"Publish failed with code {result.rc}"}
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")
            return {"error": str(e)}

    async def subscribe(self, topic: str, timeout: float = 2.0) -> List[Dict[str, Any]]:
        """Subscribe to a topic and collect messages.

        Args:
            topic: Topic pattern to subscribe to (supports + and # wildcards)
            timeout: How long to wait for messages (seconds)

        Returns:
            List of received messages
        """
        with self._lock:
            self._messages.clear()

        try:
            result, mid = self._client.subscribe(topic)
            if result != mqtt.MQTT_ERR_SUCCESS:
                return [{"error": f"Subscribe failed with code {result}"}]

            logger.info(f"Subscribed to {topic}, waiting {timeout}s for messages")
            time.sleep(timeout)

            with self._lock:
                messages = []
                for topic_messages in self._messages.values():
                    for msg in topic_messages:
                        messages.append({
                            "topic": msg.topic,
                            "payload": msg.payload,
                            "retain": str(msg.retain),
                            "qos": str(msg.qos)
                        })
                return messages

        except Exception as e:
            logger.error(f"Error subscribing to {topic}: {e}")
            return [{"error": str(e)}]

    async def get_retained(self, topic: str, timeout: float = 1.0) -> List[Dict[str, Any]]:
        """Get retained messages from a topic pattern.

        Args:
            topic: Topic pattern (supports + and # wildcards)
            timeout: How long to wait for retained messages

        Returns:
            List of retained messages found
        """
        with self._lock:
            self._messages.clear()

        try:
            result, mid = self._client.subscribe(topic)
            if result != mqtt.MQTT_ERR_SUCCESS:
                return [{"error": f"Subscribe failed with code {result}"}]

            logger.debug(f"Subscribed to {topic} for retained messages")
            time.sleep(timeout)

            self._client.unsubscribe(topic)

            with self._lock:
                messages = []
                for topic_messages in self._messages.values():
                    for msg in topic_messages:
                        if msg.retain:
                            messages.append({
                                "topic": msg.topic,
                                "payload": msg.payload,
                                "retain": str(msg.retain)
                            })
                return messages

        except Exception as e:
            logger.error(f"Error getting retained from {topic}: {e}")
            return [{"error": str(e)}]

    async def unsubscribe(self, topic: str) -> Dict[str, Any]:
        """Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from

        Returns:
            Dict with success status
        """
        try:
            result, mid = self._client.unsubscribe(topic)
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Unsubscribed from {topic}")
                return {"topic": topic, "status": "unsubscribed"}
            else:
                return {"error": f"Unsubscribe failed with code {result}"}
        except Exception as e:
            logger.error(f"Error unsubscribing from {topic}: {e}")
            return {"error": str(e)}
