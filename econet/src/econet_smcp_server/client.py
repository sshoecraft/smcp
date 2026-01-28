"""Self-contained Rheem EcoNet client using ClearBlade API."""

import json
import logging
import ssl
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

# ClearBlade API constants
HOST = "rheem.clearblade.com"
REST_URL = f"https://{HOST}/api/v/1"
MQTT_PORT = 1884
SYSTEM_KEY = "e2e699cb0bb0bbb88fc8858cb5a401"
SYSTEM_SECRET = "E2E699CB0BE6C6FADDB1B0BC9A20"


@dataclass
class EcoNetConfig:
    """Configuration for EcoNet API."""

    email: str
    password: str

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "EcoNetConfig":
        """Create config from SMCP credentials."""
        email = creds.get("ECONET_EMAIL")
        password = creds.get("ECONET_PASSWORD")

        if not email:
            raise ValueError("ECONET_EMAIL credential is required")
        if not password:
            raise ValueError("ECONET_PASSWORD credential is required")

        return cls(email=email, password=password)


@dataclass
class WaterHeater:
    """Water heater device."""

    device_id: str
    serial_number: str
    name: str
    enabled: bool = False
    running: bool = False
    running_status: str = ""
    mode: int = 0
    mode_name: str = ""
    available_modes: List[str] = field(default_factory=list)
    setpoint: int = 120
    setpoint_min: int = 90
    setpoint_max: int = 140
    hot_water_level: int = 0
    connected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "device_id": self.device_id,
            "serial_number": self.serial_number,
            "name": self.name,
            "type": "water_heater",
            "enabled": self.enabled,
            "running": self.running,
            "running_status": self.running_status,
            "mode": self.mode_name,
            "mode_index": self.mode,
            "available_modes": self.available_modes,
            "setpoint": self.setpoint,
            "setpoint_min": self.setpoint_min,
            "setpoint_max": self.setpoint_max,
            "hot_water_level": self.hot_water_level,
            "connected": self.connected,
        }


@dataclass
class Thermostat:
    """Thermostat device."""

    device_id: str
    serial_number: str
    name: str
    enabled: bool = False
    running: bool = False
    running_status: str = ""
    mode: int = 0
    mode_name: str = ""
    available_modes: List[str] = field(default_factory=list)
    heat_setpoint: int = 70
    cool_setpoint: int = 78
    humidity: int = 0
    fan_mode: int = 0
    fan_speed: int = 0
    connected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "device_id": self.device_id,
            "serial_number": self.serial_number,
            "name": self.name,
            "type": "thermostat",
            "enabled": self.enabled,
            "running": self.running,
            "running_status": self.running_status,
            "mode": self.mode_name,
            "mode_index": self.mode,
            "available_modes": self.available_modes,
            "heat_setpoint": self.heat_setpoint,
            "cool_setpoint": self.cool_setpoint,
            "humidity": self.humidity,
            "fan_mode": self.fan_mode,
            "fan_speed": self.fan_speed,
            "connected": self.connected,
        }


class EcoNetClient:
    """Self-contained EcoNet client."""

    def __init__(self, config: EcoNetConfig):
        self.config = config
        self.session = requests.Session()
        self.user_token: str = ""
        self.account_id: str = ""
        self.mqtt_client: Optional[mqtt.Client] = None
        self.water_heaters: Dict[str, WaterHeater] = {}
        self.thermostats: Dict[str, Thermostat] = {}
        self.connected = False
        self.mqtt_connected = False
        self.lock = threading.Lock()

        logger.info("EcoNet client initialized")

    def _base_headers(self) -> Dict[str, str]:
        """Get base headers with system credentials."""
        return {
            "Content-Type": "application/json; charset=UTF-8",
            "ClearBlade-SystemKey": SYSTEM_KEY,
            "ClearBlade-SystemSecret": SYSTEM_SECRET,
        }

    def _auth_headers(self) -> Dict[str, str]:
        """Get headers with user token."""
        headers = self._base_headers()
        headers["ClearBlade-UserToken"] = self.user_token
        return headers

    def connect(self) -> None:
        """Connect to EcoNet (login + MQTT)."""
        self._login()
        self._fetch_equipment()
        self._connect_mqtt()
        self.connected = True
        logger.info("EcoNet client connected")

    def disconnect(self) -> None:
        """Disconnect from EcoNet."""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.mqtt_client = None
        self.connected = False
        self.mqtt_connected = False
        logger.info("EcoNet client disconnected")

    def _login(self) -> None:
        """Login to EcoNet and get user token."""
        url = f"{REST_URL}/user/auth"
        payload = {
            "email": self.config.email,
            "password": self.config.password,
        }

        response = self.session.post(
            url,
            headers=self._base_headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        self.user_token = data.get("user_token", "")
        options = data.get("options", {})
        self.account_id = options.get("account_id", "")

        if not self.user_token or not self.account_id:
            raise ValueError("Login failed: missing user_token or account_id")

        logger.info(f"Logged in as {self.config.email}")

    def _fetch_equipment(self) -> None:
        """Fetch equipment list from EcoNet."""
        url = f"{REST_URL}/code/{SYSTEM_KEY}/getUserDataForApp"
        payload = {"resource": "friedrich"}

        response = self.session.post(
            url,
            headers=self._auth_headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", {})
        locations = results.get("locations", [])

        for location in locations:
            equipments = location.get("equiptments", [])
            for eq in equipments:
                self._parse_equipment(eq)

        logger.info(f"Found {len(self.water_heaters)} water heater(s), "
                    f"{len(self.thermostats)} thermostat(s)")

    def _parse_equipment(self, eq: Dict[str, Any]) -> None:
        """Parse equipment data into device objects."""
        device_type = eq.get("device_type", "")
        device_id = eq.get("device_name", "")
        serial = eq.get("serial_number", "")

        if device_type == "WH":
            wh = WaterHeater(
                device_id=device_id,
                serial_number=serial,
                name=self._get_field_value(eq, "@NAME", device_id),
            )
            self._update_water_heater(wh, eq)
            self.water_heaters[device_id] = wh

        elif device_type == "HVAC":
            th = Thermostat(
                device_id=device_id,
                serial_number=serial,
                name=self._get_field_value(eq, "@NAME", device_id),
            )
            self._update_thermostat(th, eq)
            self.thermostats[device_id] = th

    def _get_field_value(self, eq: Dict, field_name: str, default: Any = None) -> Any:
        """Get field value, handling both direct and nested formats."""
        val = eq.get(field_name)
        if val is None:
            return default
        if isinstance(val, dict):
            return val.get("value", default)
        return val

    def _get_field_constraints(self, eq: Dict, field_name: str) -> Dict:
        """Get field constraints."""
        val = eq.get(field_name)
        if isinstance(val, dict):
            return val.get("constraints", {})
        return {}

    def _update_water_heater(self, wh: WaterHeater, eq: Dict) -> None:
        """Update water heater from equipment data."""
        wh.enabled = bool(self._get_field_value(eq, "@ENABLED", 0))
        wh.running = "@RUNNING" in eq
        wh.running_status = str(self._get_field_value(eq, "@RUNNING", ""))
        wh.connected = eq.get("@CONNECTED", False)

        # Mode
        wh.mode = int(self._get_field_value(eq, "@MODE", 0))
        constraints = self._get_field_constraints(eq, "@MODE")
        wh.available_modes = constraints.get("enumText", [])
        if wh.available_modes and 0 <= wh.mode < len(wh.available_modes):
            wh.mode_name = wh.available_modes[wh.mode]

        # Setpoint
        wh.setpoint = int(self._get_field_value(eq, "@SETPOINT", 120))
        sp_constraints = self._get_field_constraints(eq, "@SETPOINT")
        wh.setpoint_min = sp_constraints.get("lowerLimit", 90)
        wh.setpoint_max = sp_constraints.get("upperLimit", 140)

        # Hot water level
        hotwater = str(self._get_field_value(eq, "@HOTWATER", "")).lower()
        wh.hot_water_level = self._parse_hotwater_level(hotwater)

    def _update_thermostat(self, th: Thermostat, eq: Dict) -> None:
        """Update thermostat from equipment data."""
        th.enabled = bool(self._get_field_value(eq, "@ENABLED", 0))
        th.running = "@RUNNINGSTATUS" in eq
        th.running_status = str(self._get_field_value(eq, "@RUNNINGSTATUS", ""))
        th.connected = eq.get("@CONNECTED", False)

        # Mode
        th.mode = int(self._get_field_value(eq, "@MODE", 0))
        constraints = self._get_field_constraints(eq, "@MODE")
        th.available_modes = constraints.get("enumText", [])
        if th.available_modes and 0 <= th.mode < len(th.available_modes):
            th.mode_name = th.available_modes[th.mode]

        # Setpoints
        th.heat_setpoint = int(self._get_field_value(eq, "@HEATSETPOINT", 70))
        th.cool_setpoint = int(self._get_field_value(eq, "@COOLSETPOINT", 78))

        # Other
        th.humidity = int(self._get_field_value(eq, "@HUMIDITY", 0))
        th.fan_mode = int(self._get_field_value(eq, "@FANMODE", 0))
        th.fan_speed = int(self._get_field_value(eq, "@FANSPEED", 0))

    def _parse_hotwater_level(self, level: str) -> int:
        """Parse hot water level string to percentage."""
        level = level.lower()
        if "hund" in level or level == "100":
            return 100
        if "fourty" in level or "forty" in level or level == "40":
            return 40
        if "ten" in level or level == "10":
            return 10
        if "empty" in level or "zero" in level or level == "0":
            return 0
        return 0

    def _connect_mqtt(self) -> None:
        """Connect to MQTT for real-time updates."""
        client_id = f"{self.config.email}{int(time.time() * 1000)}_android"

        self.mqtt_client = mqtt.Client(
            client_id=client_id,
            protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )

        # TLS
        self.mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.mqtt_client.tls_insecure_set(True)

        # Auth: token as username, system_key as password
        self.mqtt_client.username_pw_set(self.user_token, SYSTEM_KEY)

        # Callbacks
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect

        # Connect
        self.mqtt_client.connect(HOST, MQTT_PORT, keepalive=60)
        self.mqtt_client.loop_start()

        # Wait for connection
        timeout = 10
        start = time.time()
        while not self.mqtt_connected and (time.time() - start) < timeout:
            time.sleep(0.1)

        if not self.mqtt_connected:
            logger.warning("MQTT connection timeout, continuing without real-time updates")

    def _on_mqtt_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        """Handle MQTT connect."""
        if reason_code == 0:
            self.mqtt_connected = True
            logger.info("MQTT connected")

            # Subscribe to reported state
            topic = f"user/{self.account_id}/device/reported"
            client.subscribe(topic)
            logger.debug(f"Subscribed to {topic}")
        else:
            logger.error(f"MQTT connect failed: {reason_code}")

    def _on_mqtt_disconnect(self, client, userdata, flags, reason_code, properties=None) -> None:
        """Handle MQTT disconnect."""
        self.mqtt_connected = False
        logger.warning(f"MQTT disconnected: {reason_code}")

    def _on_mqtt_message(self, client, userdata, msg) -> None:
        """Handle MQTT message (device state update)."""
        try:
            payload = json.loads(msg.payload.decode())
            device_id = payload.get("device_name", "")

            with self.lock:
                if device_id in self.water_heaters:
                    self._update_water_heater_from_mqtt(device_id, payload)
                elif device_id in self.thermostats:
                    self._update_thermostat_from_mqtt(device_id, payload)

        except Exception as e:
            logger.debug(f"Error processing MQTT message: {e}")

    def _update_water_heater_from_mqtt(self, device_id: str, payload: Dict) -> None:
        """Update water heater from MQTT payload."""
        wh = self.water_heaters.get(device_id)
        if not wh:
            return

        if "@ENABLED" in payload:
            wh.enabled = bool(payload["@ENABLED"])
        if "@MODE" in payload:
            wh.mode = int(payload["@MODE"])
            if wh.available_modes and 0 <= wh.mode < len(wh.available_modes):
                wh.mode_name = wh.available_modes[wh.mode]
        if "@SETPOINT" in payload:
            wh.setpoint = int(payload["@SETPOINT"])
        if "@RUNNING" in payload:
            wh.running = True
            wh.running_status = str(payload["@RUNNING"])
        if "@HOTWATER" in payload:
            wh.hot_water_level = self._parse_hotwater_level(str(payload["@HOTWATER"]))

    def _update_thermostat_from_mqtt(self, device_id: str, payload: Dict) -> None:
        """Update thermostat from MQTT payload."""
        th = self.thermostats.get(device_id)
        if not th:
            return

        if "@ENABLED" in payload:
            th.enabled = bool(payload["@ENABLED"])
        if "@MODE" in payload:
            th.mode = int(payload["@MODE"])
            if th.available_modes and 0 <= th.mode < len(th.available_modes):
                th.mode_name = th.available_modes[th.mode]
        if "@HEATSETPOINT" in payload:
            th.heat_setpoint = int(payload["@HEATSETPOINT"])
        if "@COOLSETPOINT" in payload:
            th.cool_setpoint = int(payload["@COOLSETPOINT"])
        if "@HUMIDITY" in payload:
            th.humidity = int(payload["@HUMIDITY"])

    def _publish_mqtt(self, device_id: str, serial: str, updates: Dict) -> None:
        """Publish control message to MQTT."""
        if not self.mqtt_client or not self.mqtt_connected:
            raise ValueError("MQTT not connected")

        topic = f"user/{self.account_id}/device/desired"
        payload = {
            "transactionId": f"ANDROID_{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}",
            "device_name": device_id,
            "serial_number": serial,
            **updates,
        }

        self.mqtt_client.publish(topic, json.dumps(payload))
        logger.debug(f"Published to {topic}: {payload}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def get_equipment(self) -> List[Dict[str, Any]]:
        """Get all equipment."""
        result = []
        with self.lock:
            for wh in self.water_heaters.values():
                result.append(wh.to_dict())
            for th in self.thermostats.values():
                result.append(th.to_dict())
        return result

    def get_water_heaters(self) -> List[Dict[str, Any]]:
        """Get all water heaters."""
        with self.lock:
            return [wh.to_dict() for wh in self.water_heaters.values()]

    def get_water_heater(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific water heater or the first one."""
        with self.lock:
            if device_id:
                wh = self.water_heaters.get(device_id)
                if not wh:
                    raise ValueError(f"Water heater {device_id} not found")
                return wh.to_dict()
            elif self.water_heaters:
                return next(iter(self.water_heaters.values())).to_dict()
            else:
                raise ValueError("No water heaters found")

    def set_water_heater_mode(self, mode: str, device_id: Optional[str] = None) -> None:
        """Set water heater mode."""
        with self.lock:
            if device_id:
                wh = self.water_heaters.get(device_id)
            elif self.water_heaters:
                wh = next(iter(self.water_heaters.values()))
            else:
                raise ValueError("No water heaters found")

            if not wh:
                raise ValueError(f"Water heater {device_id} not found")

            # Find mode index
            mode_lower = mode.lower().replace(" ", "_").replace("-", "_")
            mode_index = None

            for i, m in enumerate(wh.available_modes):
                m_normalized = m.lower().replace(" ", "_").replace("-", "_")
                if m_normalized == mode_lower:
                    mode_index = i
                    break

            # Also check common aliases
            mode_aliases = {
                "off": ["off"],
                "energy_saving": ["energy_saving", "energy_saver", "energysaving"],
                "heat_pump_only": ["heat_pump_only", "heat_pump", "heatpump"],
                "high_demand": ["high_demand", "highdemand"],
                "electric_mode": ["electric_mode", "electric"],
                "vacation": ["vacation"],
                "performance": ["performance"],
            }

            if mode_index is None:
                for i, m in enumerate(wh.available_modes):
                    m_normalized = m.lower().replace(" ", "_").replace("-", "_")
                    for key, aliases in mode_aliases.items():
                        if mode_lower in aliases and m_normalized in aliases:
                            mode_index = i
                            break
                    if mode_index is not None:
                        break

            if mode_index is None:
                raise ValueError(f"Unknown mode: {mode}. Available: {wh.available_modes}")

            # Determine enabled state
            enabled = 1 if mode_lower != "off" else 0

            self._publish_mqtt(wh.device_id, wh.serial_number, {
                "@MODE": mode_index,
                "@ENABLED": enabled,
            })

            # Update local state
            wh.mode = mode_index
            wh.mode_name = wh.available_modes[mode_index]
            wh.enabled = bool(enabled)

    def set_water_heater_temperature(self, temperature: int, device_id: Optional[str] = None) -> None:
        """Set water heater temperature."""
        with self.lock:
            if device_id:
                wh = self.water_heaters.get(device_id)
            elif self.water_heaters:
                wh = next(iter(self.water_heaters.values()))
            else:
                raise ValueError("No water heaters found")

            if not wh:
                raise ValueError(f"Water heater {device_id} not found")

            if temperature < wh.setpoint_min or temperature > wh.setpoint_max:
                raise ValueError(f"Temperature must be between {wh.setpoint_min} and {wh.setpoint_max}")

            self._publish_mqtt(wh.device_id, wh.serial_number, {
                "@SETPOINT": temperature,
            })

            wh.setpoint = temperature

    def get_thermostats(self) -> List[Dict[str, Any]]:
        """Get all thermostats."""
        with self.lock:
            return [th.to_dict() for th in self.thermostats.values()]

    def get_thermostat(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific thermostat or the first one."""
        with self.lock:
            if device_id:
                th = self.thermostats.get(device_id)
                if not th:
                    raise ValueError(f"Thermostat {device_id} not found")
                return th.to_dict()
            elif self.thermostats:
                return next(iter(self.thermostats.values())).to_dict()
            else:
                raise ValueError("No thermostats found")

    def get_energy_usage(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get water heater energy usage."""
        with self.lock:
            if device_id:
                wh = self.water_heaters.get(device_id)
            elif self.water_heaters:
                wh = next(iter(self.water_heaters.values()))
            else:
                raise ValueError("No water heaters found")

            if not wh:
                raise ValueError(f"Water heater {device_id} not found")

            wh_copy = WaterHeater(
                device_id=wh.device_id,
                serial_number=wh.serial_number,
                name=wh.name,
            )

        url = f"{REST_URL}/code/{SYSTEM_KEY}/dynamicAction"
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        payload = {
            "ACTION": "waterheaterUsageReportView",
            "device_name": wh_copy.device_id,
            "serial_number": wh_copy.serial_number,
            "start_date": start.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "end_date": now.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "usage_type": "energyUsage",
        }

        response = self.session.post(
            url,
            headers=self._auth_headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", {})
        energy = results.get("energy_usage", {})

        return {
            "device_id": wh_copy.device_id,
            "message": energy.get("message", ""),
            "data": energy.get("data", []),
        }

    def get_water_usage(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get water heater water usage."""
        with self.lock:
            if device_id:
                wh = self.water_heaters.get(device_id)
            elif self.water_heaters:
                wh = next(iter(self.water_heaters.values()))
            else:
                raise ValueError("No water heaters found")

            if not wh:
                raise ValueError(f"Water heater {device_id} not found")

            wh_copy = WaterHeater(
                device_id=wh.device_id,
                serial_number=wh.serial_number,
                name=wh.name,
            )

        url = f"{REST_URL}/code/{SYSTEM_KEY}/dynamicAction"
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        payload = {
            "ACTION": "waterheaterUsageReportView",
            "device_name": wh_copy.device_id,
            "serial_number": wh_copy.serial_number,
            "start_date": start.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "end_date": now.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "usage_type": "waterUsage",
        }

        response = self.session.post(
            url,
            headers=self._auth_headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", {})
        water = results.get("water_usage", {})

        return {
            "device_id": wh_copy.device_id,
            "data": water.get("data", []),
        }
