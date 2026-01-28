"""HomeKit client wrapper using aiohomekit library."""

import logging
import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from aiohomekit import Controller
from aiohomekit.model.services import ServicesTypes
from aiohomekit.model.characteristics import CharacteristicsTypes
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser
from zeroconf import ServiceListener

logger = logging.getLogger(__name__)

# Build reverse lookup dicts for UUID -> short name
SERVICE_UUID_TO_NAME = {
    getattr(ServicesTypes, name): name.lower().replace('_', '-')
    for name in dir(ServicesTypes)
    if not name.startswith('_') and isinstance(getattr(ServicesTypes, name), str)
}

CHAR_UUID_TO_NAME = {
    getattr(CharacteristicsTypes, name): name.lower().replace('_', '-')
    for name in dir(CharacteristicsTypes)
    if not name.startswith('_') and isinstance(getattr(CharacteristicsTypes, name), str)
}

HAP_TYPE_TCP = "_hap._tcp.local."
HAP_TYPE_UDP = "_hap._udp.local."


class _HapListener(ServiceListener):
    """Empty listener required by zeroconf browser."""
    def add_service(self, zc, type_, name):
        pass
    def remove_service(self, zc, type_, name):
        pass
    def update_service(self, zc, type_, name):
        pass


@dataclass
class HomeKitConfig:
    """Configuration for HomeKit client."""
    pairing_data: Dict[str, Any]
    read_only: bool = False

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "HomeKitConfig":
        """Create config from SMCP credentials."""
        pairing_data_str = creds.get("HOMEKIT_PAIRING_DATA")
        if not pairing_data_str:
            raise ValueError("HOMEKIT_PAIRING_DATA credential is required")

        try:
            pairing_data = json.loads(pairing_data_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"HOMEKIT_PAIRING_DATA must be valid JSON: {e}")

        return cls(
            pairing_data=pairing_data,
            read_only=creds.get("READ_ONLY_MODE", "false").lower() == "true",
        )


class HomeKitError(Exception):
    """HomeKit operation error."""
    pass


class HomeKitClient:
    """HomeKit client wrapper for local device control using aiohomekit."""

    def __init__(self, config: HomeKitConfig):
        """Initialize the HomeKit client."""
        self.config = config
        self.read_only = config.read_only
        self.alias = config.pairing_data.get("alias", "homekit_device")
        self._pairing_data = config.pairing_data

        # These get initialized in _ensure_connected
        self._azc = None
        self._browser_tcp = None
        self._browser_udp = None
        self.controller = None
        self.pairing = None

    async def _ensure_connected(self) -> None:
        """Ensure we have an active pairing connection."""
        if self.pairing is None:
            # Set up zeroconf with browsers for HAP protocols
            self._azc = AsyncZeroconf()
            listener = _HapListener()
            self._browser_tcp = AsyncServiceBrowser(self._azc.zeroconf, HAP_TYPE_TCP, listener)
            self._browser_udp = AsyncServiceBrowser(self._azc.zeroconf, HAP_TYPE_UDP, listener)

            # Create controller and start it
            self.controller = Controller(async_zeroconf_instance=self._azc)
            await self.controller.async_start()

            # Load pairing from stored data
            self.pairing = self.controller.load_pairing(self.alias, self._pairing_data)
            logger.info(f"Loaded pairing for device: {self.alias}")

    def _get_service_type_name(self, service_type: str) -> str:
        """Get human-readable service type name."""
        return SERVICE_UUID_TO_NAME.get(service_type, service_type)

    def _get_char_type_name(self, char_type: str) -> str:
        """Get human-readable characteristic type name."""
        return CHAR_UUID_TO_NAME.get(char_type, char_type)

    async def list_accessories(self) -> List[Dict[str, Any]]:
        """List all accessories and their services."""
        try:
            await self._ensure_connected()
            accessories_data = await self.pairing.list_accessories_and_characteristics()

            result = []
            for accessory in accessories_data:
                acc_info = {
                    "aid": accessory["aid"],
                    "services": []
                }

                for service in accessory.get("services", []):
                    svc_info = {
                        "type": self._get_service_type_name(service.get("type", "")),
                        "iid": service.get("iid"),
                        "characteristics": []
                    }

                    for char in service.get("characteristics", []):
                        char_info = {
                            "type": self._get_char_type_name(char.get("type", "")),
                            "iid": char.get("iid"),
                            "format": char.get("format", ""),
                            "perms": char.get("perms", []),
                            "value": char.get("value")
                        }
                        svc_info["characteristics"].append(char_info)

                    acc_info["services"].append(svc_info)

                result.append(acc_info)

            return result
        except Exception as e:
            logger.error(f"Error listing accessories: {e}")
            raise HomeKitError(f"Failed to list accessories: {e}")

    async def get_characteristics(
        self,
        characteristics: List[tuple]
    ) -> Dict[str, Any]:
        """Get characteristic values.

        Args:
            characteristics: List of (aid, iid) tuples
        """
        try:
            await self._ensure_connected()
            result = await self.pairing.get_characteristics(characteristics)

            # Convert to more readable format
            formatted = {}
            for key, value in result.items():
                aid, iid = key
                formatted[f"{aid}.{iid}"] = value

            return formatted
        except Exception as e:
            logger.error(f"Error getting characteristics: {e}")
            raise HomeKitError(f"Failed to get characteristics: {e}")

    async def set_characteristics(
        self,
        characteristics: Dict[tuple, Any]
    ) -> Dict[str, Any]:
        """Set characteristic values.

        Args:
            characteristics: Dict mapping (aid, iid) tuples to values
        """
        if self.read_only:
            raise HomeKitError("Cannot set characteristics in read-only mode")

        try:
            await self._ensure_connected()
            # Convert dict to list of tuples for aiohomekit
            char_list = [(aid, iid, value) for (aid, iid), value in characteristics.items()]
            await self.pairing.put_characteristics(char_list)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error setting characteristics: {e}")
            raise HomeKitError(f"Failed to set characteristics: {e}")

    async def get_accessory_info(self, aid: int = 1) -> Dict[str, Any]:
        """Get info about a specific accessory."""
        try:
            accessories = await self.list_accessories()
            for acc in accessories:
                if acc["aid"] == aid:
                    # Find accessory information service
                    for service in acc["services"]:
                        if service["type"] == "accessory-information":
                            info = {}
                            for char in service["characteristics"]:
                                info[char["type"]] = char.get("value", "")
                            return info
            return {}
        except Exception as e:
            logger.error(f"Error getting accessory info: {e}")
            raise HomeKitError(f"Failed to get accessory info: {e}")

    # Convenience methods for common device types

    async def get_light_state(self, aid: int = 1) -> Dict[str, Any]:
        """Get light bulb state."""
        try:
            accessories = await self.list_accessories()
            for acc in accessories:
                if acc["aid"] == aid:
                    for service in acc["services"]:
                        if service["type"] == "lightbulb":
                            state = {}
                            for char in service["characteristics"]:
                                if char["type"] == "on":
                                    state["on"] = char.get("value", False)
                                elif char["type"] == "brightness":
                                    state["brightness"] = char.get("value", 0)
                                elif char["type"] == "hue":
                                    state["hue"] = char.get("value", 0)
                                elif char["type"] == "saturation":
                                    state["saturation"] = char.get("value", 0)
                            return state
            return {"error": "No lightbulb service found"}
        except Exception as e:
            logger.error(f"Error getting light state: {e}")
            return {"error": str(e)}

    async def set_light_state(
        self,
        aid: int = 1,
        on: Optional[bool] = None,
        brightness: Optional[int] = None,
        hue: Optional[float] = None,
        saturation: Optional[float] = None
    ) -> Dict[str, Any]:
        """Set light bulb state."""
        if self.read_only:
            return {"success": False, "error": "Read-only mode enabled"}

        try:
            accessories = await self.list_accessories()
            chars_to_set = {}

            for acc in accessories:
                if acc["aid"] == aid:
                    for service in acc["services"]:
                        if service["type"] == "lightbulb":
                            for char in service["characteristics"]:
                                if char["type"] == "on" and on is not None:
                                    # aiohomekit requires 0/1 for booleans
                                    chars_to_set[(aid, char["iid"])] = 1 if on else 0
                                elif char["type"] == "brightness" and brightness is not None:
                                    chars_to_set[(aid, char["iid"])] = brightness
                                elif char["type"] == "hue" and hue is not None:
                                    chars_to_set[(aid, char["iid"])] = hue
                                elif char["type"] == "saturation" and saturation is not None:
                                    chars_to_set[(aid, char["iid"])] = saturation

            if chars_to_set:
                await self.set_characteristics(chars_to_set)
                return {"success": True}
            return {"success": False, "error": "No matching characteristics found"}
        except Exception as e:
            logger.error(f"Error setting light state: {e}")
            return {"success": False, "error": str(e)}

    async def get_thermostat_state(self, aid: int = 1) -> Dict[str, Any]:
        """Get thermostat state."""
        try:
            accessories = await self.list_accessories()
            for acc in accessories:
                if acc["aid"] == aid:
                    for service in acc["services"]:
                        if service["type"] == "thermostat":
                            state = {}
                            for char in service["characteristics"]:
                                char_type = char["type"]
                                value = char.get("value")
                                # aiohomekit uses different names than Apple's spec
                                if char_type in ("temperature-current", "current-temperature"):
                                    state["current_temperature"] = value
                                elif char_type in ("temperature-target", "target-temperature"):
                                    state["target_temperature"] = value
                                elif char_type in ("heating-cooling-current", "current-heating-cooling-state"):
                                    states = {0: "off", 1: "heating", 2: "cooling"}
                                    state["current_state"] = states.get(value, str(value))
                                elif char_type in ("heating-cooling-target", "target-heating-cooling-state"):
                                    states = {0: "off", 1: "heat", 2: "cool", 3: "auto"}
                                    state["target_state"] = states.get(value, str(value))
                                elif char_type in ("temperature-heating-threshold", "heating-threshold-temperature"):
                                    state["heating_threshold"] = value
                                elif char_type in ("temperature-cooling-threshold", "cooling-threshold-temperature"):
                                    state["cooling_threshold"] = value
                                elif char_type in ("relative-humidity-current", "current-relative-humidity"):
                                    state["humidity"] = value
                            return state
            return {"error": "No thermostat service found"}
        except Exception as e:
            logger.error(f"Error getting thermostat state: {e}")
            return {"error": str(e)}

    async def set_thermostat_state(
        self,
        aid: int = 1,
        target_temperature: Optional[float] = None,
        target_state: Optional[str] = None,
        heating_threshold: Optional[float] = None,
        cooling_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Set thermostat state."""
        if self.read_only:
            return {"success": False, "error": "Read-only mode enabled"}

        try:
            state_map = {"off": 0, "heat": 1, "cool": 2, "auto": 3}
            accessories = await self.list_accessories()
            chars_to_set = {}

            for acc in accessories:
                if acc["aid"] == aid:
                    for service in acc["services"]:
                        if service["type"] == "thermostat":
                            for char in service["characteristics"]:
                                char_type = char["type"]
                                if char_type in ("temperature-target", "target-temperature") and target_temperature is not None:
                                    chars_to_set[(aid, char["iid"])] = target_temperature
                                elif char_type in ("heating-cooling-target", "target-heating-cooling-state") and target_state is not None:
                                    if target_state in state_map:
                                        chars_to_set[(aid, char["iid"])] = state_map[target_state]
                                elif char_type in ("temperature-heating-threshold", "heating-threshold-temperature") and heating_threshold is not None:
                                    chars_to_set[(aid, char["iid"])] = heating_threshold
                                elif char_type in ("temperature-cooling-threshold", "cooling-threshold-temperature") and cooling_threshold is not None:
                                    chars_to_set[(aid, char["iid"])] = cooling_threshold

            if chars_to_set:
                await self.set_characteristics(chars_to_set)
                return {"success": True}
            return {"success": False, "error": "No matching characteristics found"}
        except Exception as e:
            logger.error(f"Error setting thermostat state: {e}")
            return {"success": False, "error": str(e)}

    async def get_sensor_values(self, aid: int = 1) -> Dict[str, Any]:
        """Get sensor values (temperature, humidity, motion, contact, etc.)."""
        try:
            accessories = await self.list_accessories()
            sensors = {}

            for acc in accessories:
                if acc["aid"] == aid:
                    for service in acc["services"]:
                        svc_type = service["type"]
                        if svc_type in ["temperature-sensor", "humidity-sensor",
                                        "motion-sensor", "contact-sensor",
                                        "leak-sensor", "smoke-sensor",
                                        "light-sensor", "occupancy-sensor"]:
                            for char in service["characteristics"]:
                                char_type = char["type"]
                                value = char.get("value")
                                if char_type in ("temperature-current", "current-temperature"):
                                    sensors["temperature"] = value
                                elif char_type in ("relative-humidity-current", "current-relative-humidity"):
                                    sensors["humidity"] = value
                                elif char_type in ("motion-detected",):
                                    sensors["motion"] = value
                                elif char_type in ("contact-state", "contact-sensor-state"):
                                    sensors["contact"] = "open" if value == 1 else "closed"
                                elif char_type in ("leak-detected",):
                                    sensors["leak"] = value == 1
                                elif char_type in ("smoke-detected",):
                                    sensors["smoke"] = value == 1
                                elif char_type in ("light-level-current", "current-ambient-light-level"):
                                    sensors["light_level"] = value
                                elif char_type in ("occupancy-detected",):
                                    sensors["occupancy"] = value == 1

            return sensors if sensors else {"error": "No sensor services found"}
        except Exception as e:
            logger.error(f"Error getting sensor values: {e}")
            return {"error": str(e)}

    async def close(self) -> None:
        """Close the connection."""
        if self.pairing:
            try:
                await self.pairing.close()
            except Exception:
                pass
            self.pairing = None

        if self.controller:
            try:
                await self.controller.async_stop()
            except Exception:
                pass
            self.controller = None

        if self._browser_tcp:
            try:
                await self._browser_tcp.async_cancel()
            except Exception:
                pass
            self._browser_tcp = None

        if self._browser_udp:
            try:
                await self._browser_udp.async_cancel()
            except Exception:
                pass
            self._browser_udp = None

        if self._azc:
            try:
                await self._azc.async_close()
            except Exception:
                pass
            self._azc = None
