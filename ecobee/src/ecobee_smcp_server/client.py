"""Ecobee API client wrapper."""

import logging
import json
import copy
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

import requests

logger = logging.getLogger(__name__)

URL_BASE = "https://api.ecobee.com/"
API_VERSION = "1/"


@dataclass
class EcobeeConfig:
    """Configuration for Ecobee client."""
    api_key: str
    access_token: str
    refresh_token: str
    thermostat_id: Optional[str] = None
    read_only: bool = True

    @classmethod
    def from_smcp_creds(cls, creds: Dict[str, str]) -> "EcobeeConfig":
        """Create config from SMCP credentials."""
        api_key = creds.get("ECOBEE_API_KEY")
        if not api_key:
            raise ValueError("ECOBEE_API_KEY credential is required")

        access_token = creds.get("ACCESS_TOKEN")
        if not access_token:
            raise ValueError("ACCESS_TOKEN credential is required")

        refresh_token = creds.get("REFRESH_TOKEN")
        if not refresh_token:
            raise ValueError("REFRESH_TOKEN credential is required")

        return cls(
            api_key=api_key,
            access_token=access_token,
            refresh_token=refresh_token,
            thermostat_id=creds.get("THERMOSTAT_ID"),
            read_only=creds.get("READ_ONLY_MODE", "true").lower() == "true",
        )


class EcobeeError(Exception):
    """Ecobee API error."""
    pass


class ExpiredTokenError(EcobeeError):
    """Access token has expired."""
    pass


class EcobeeClient:
    """Ecobee API client wrapper."""

    THERMOSTAT_URL = URL_BASE + API_VERSION + "thermostat"
    TOKEN_URL = URL_BASE + "token"

    # API response codes
    SUCCESS = 0
    EXPIRED_TOKEN = 14

    def __init__(self, config: EcobeeConfig):
        """Initialize the Ecobee client."""
        self.config = config
        self.api_key = config.api_key
        self.access_token = config.access_token
        self.refresh_token = config.refresh_token
        self.default_thermostat_id = config.thermostat_id
        self.read_only = config.read_only

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with current access token."""
        return {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": f"Bearer {self.access_token}"
        }

    def _refresh_tokens(self) -> None:
        """Refresh the access and refresh tokens."""
        logger.info("Refreshing access token")
        params = {
            "grant_type": "refresh_token",
            "code": self.refresh_token,
            "client_id": self.api_key
        }
        resp = requests.post(self.TOKEN_URL, params=params)
        data = resp.json()

        if "access_token" in data:
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            logger.info("Token refresh successful")
        else:
            raise EcobeeError(f"Token refresh failed: {data}")

    def _format_selection(self, thermostat_id: str, **kwargs) -> Dict[str, Any]:
        """Format the selection object for API requests."""
        selection = {
            "selectionType": "thermostats",
            "selectionMatch": thermostat_id
        }
        selection.update(kwargs)
        return selection

    def _send_request(self, method: str, body: Dict[str, Any], thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a request to the Ecobee API with automatic token refresh."""
        tstat_id = thermostat_id or self.default_thermostat_id
        if not tstat_id:
            raise EcobeeError("No thermostat_id provided and no default set")

        # Add selection to body
        selection = body.pop("selection", {})
        body["selection"] = self._format_selection(tstat_id, **selection)

        try:
            return self._execute_request(method, body)
        except ExpiredTokenError:
            self._refresh_tokens()
            return self._execute_request(method, body)

    def _execute_request(self, method: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual HTTP request."""
        headers = self._get_headers()

        if method == "GET":
            params = {"format": "json", "body": json.dumps(body)}
            resp = requests.get(self.THERMOSTAT_URL, headers=headers, params=params)
        else:
            params = {"format": "json"}
            resp = requests.post(self.THERMOSTAT_URL, headers=headers, params=params, data=json.dumps(body))

        data = resp.json()
        code = data.get("status", {}).get("code", -1)

        if code == self.SUCCESS:
            return data
        elif code == self.EXPIRED_TOKEN:
            raise ExpiredTokenError("Access token expired")
        else:
            msg = data.get("status", {}).get("message", "Unknown error")
            raise EcobeeError(f"API error {code}: {msg}")

    def _send_get(self, body: Dict[str, Any], thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a GET request."""
        data = self._send_request("GET", body, thermostat_id)
        return data.get("thermostatList", [{}])[0]

    def _send_post(self, body: Dict[str, Any], thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a POST request."""
        return self._send_request("POST", body, thermostat_id)

    def _send_function(self, func_type: str, params: Dict[str, Any], thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a function request (like setHold, resumeProgram, etc.)."""
        body = {
            "functions": [{"type": func_type, "params": params}]
        }
        return self._send_post(body, thermostat_id)

    # Read operations

    async def list_thermostats(self) -> List[Dict[str, str]]:
        """List all thermostats for the account."""
        try:
            headers = self._get_headers()
            selection = {"selectionType": "registered", "selectionMatch": ""}
            params = {"format": "json", "body": json.dumps({"selection": selection})}

            try:
                resp = requests.get(self.THERMOSTAT_URL, headers=headers, params=params)
                data = resp.json()
            except Exception:
                self._refresh_tokens()
                headers = self._get_headers()
                resp = requests.get(self.THERMOSTAT_URL, headers=headers, params=params)
                data = resp.json()

            thermostats = []
            for tstat in data.get("thermostatList", []):
                thermostats.append({
                    "identifier": tstat.get("identifier", ""),
                    "name": tstat.get("name", ""),
                    "model": tstat.get("modelNumber", "")
                })
            return thermostats
        except Exception as e:
            logger.error(f"Error listing thermostats: {e}")
            return []

    async def get_thermostat_info(self, thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Get basic thermostat info including time and location."""
        try:
            body = {"selection": {"includeLocation": True}}
            data = self._send_get(body, thermostat_id)
            return {
                "identifier": data.get("identifier", ""),
                "name": data.get("name", ""),
                "utc_time": data.get("utcTime", ""),
                "thermostat_time": data.get("thermostatTime", ""),
                "location": data.get("location", {})
            }
        except Exception as e:
            logger.error(f"Error getting thermostat info: {e}")
            return {"error": str(e)}

    async def get_temperature(self, thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current temperature reading."""
        try:
            body = {"selection": {"includeRuntime": True, "includeSensors": True}}
            data = self._send_get(body, thermostat_id)

            runtime = data.get("runtime", {})
            sensors = data.get("remoteSensors", [])

            # Find thermostat sensor temperature
            thermostat_temp = None
            for sensor in sensors:
                if sensor.get("type") == "thermostat":
                    for cap in sensor.get("capability", []):
                        if cap.get("type") == "temperature":
                            thermostat_temp = int(cap.get("value", 0)) / 10.0
                            break

            return {
                "temperature": thermostat_temp,
                "humidity": runtime.get("actualHumidity"),
                "desired_heat": runtime.get("desiredHeat", 0) / 10.0 if runtime.get("desiredHeat") else None,
                "desired_cool": runtime.get("desiredCool", 0) / 10.0 if runtime.get("desiredCool") else None,
                "hvac_mode": runtime.get("desiredHeatRange", [None])[0] if runtime.get("desiredHeatRange") else None,
                "last_modified": runtime.get("lastStatusModified", "")
            }
        except Exception as e:
            logger.error(f"Error getting temperature: {e}")
            return {"error": str(e)}

    async def get_sensors(self, thermostat_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all remote sensor readings."""
        try:
            body = {"selection": {"includeSensors": True}}
            data = self._send_get(body, thermostat_id)

            sensors = []
            for sensor in data.get("remoteSensors", []):
                sensor_data = {
                    "id": sensor.get("id", ""),
                    "name": sensor.get("name", ""),
                    "type": sensor.get("type", ""),
                    "in_use": sensor.get("inUse", False)
                }
                for cap in sensor.get("capability", []):
                    cap_type = cap.get("type", "")
                    value = cap.get("value", "")
                    if cap_type == "temperature" and value:
                        sensor_data["temperature"] = int(value) / 10.0
                    elif cap_type == "humidity" and value:
                        sensor_data["humidity"] = int(value)
                    elif cap_type == "occupancy":
                        sensor_data["occupancy"] = value == "true"
                sensors.append(sensor_data)
            return sensors
        except Exception as e:
            logger.error(f"Error getting sensors: {e}")
            return []

    async def get_runtime(self, thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Get runtime data."""
        try:
            body = {"selection": {"includeRuntime": True, "includeExtendedRuntime": True}}
            data = self._send_get(body, thermostat_id)
            return {
                "runtime": data.get("runtime", {}),
                "extended_runtime": data.get("extendedRuntime", {})
            }
        except Exception as e:
            logger.error(f"Error getting runtime: {e}")
            return {"error": str(e)}

    async def get_settings(self, thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Get thermostat settings."""
        try:
            body = {"selection": {"includeSettings": True}}
            data = self._send_get(body, thermostat_id)
            return data.get("settings", {})
        except Exception as e:
            logger.error(f"Error getting settings: {e}")
            return {"error": str(e)}

    async def get_program(self, thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Get the thermostat program (schedule and climates)."""
        try:
            body = {"selection": {"includeProgram": True}}
            data = self._send_get(body, thermostat_id)
            return data.get("program", {})
        except Exception as e:
            logger.error(f"Error getting program: {e}")
            return {"error": str(e)}

    async def get_events(self, thermostat_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active events."""
        try:
            body = {"selection": {"includeEvents": True}}
            data = self._send_get(body, thermostat_id)
            return data.get("events", [])
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []

    async def get_vacations(self, thermostat_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get vacation events."""
        try:
            events = await self.get_events(thermostat_id)
            return [e for e in events if e.get("type") == "vacation"]
        except Exception as e:
            logger.error(f"Error getting vacations: {e}")
            return []

    # Write operations

    async def set_temperature(
        self,
        heat_temp: float,
        cool_temp: float,
        thermostat_id: Optional[str] = None,
        hold_type: str = "nextTransition",
        hold_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """Set temperature hold."""
        if self.read_only:
            return {"success": False, "error": "Read-only mode enabled"}

        try:
            params = {
                "holdType": hold_type,
                "heatHoldTemp": int(heat_temp * 10),
                "coolHoldTemp": int(cool_temp * 10)
            }
            if hold_type == "holdHours" and hold_hours:
                params["holdHours"] = hold_hours

            self._send_function("setHold", params, thermostat_id)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error setting temperature: {e}")
            return {"success": False, "error": str(e)}

    async def set_mode(self, mode: str, thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Set HVAC mode (heat, cool, auto, off)."""
        if self.read_only:
            return {"success": False, "error": "Read-only mode enabled"}

        valid_modes = ["heat", "cool", "auto", "off"]
        if mode not in valid_modes:
            return {"success": False, "error": f"Invalid mode. Must be one of: {valid_modes}"}

        try:
            body = {"thermostat": {"settings": {"hvacMode": mode}}}
            self._send_post(body, thermostat_id)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error setting mode: {e}")
            return {"success": False, "error": str(e)}

    async def resume_program(self, thermostat_id: Optional[str] = None, resume_all: bool = False) -> Dict[str, Any]:
        """Resume the regular program, canceling any holds."""
        if self.read_only:
            return {"success": False, "error": "Read-only mode enabled"}

        try:
            params = {"resumeAll": resume_all}
            self._send_function("resumeProgram", params, thermostat_id)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error resuming program: {e}")
            return {"success": False, "error": str(e)}

    async def set_fan_mode(
        self,
        fan_mode: str,
        thermostat_id: Optional[str] = None,
        fan_min_on_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """Set fan mode (auto, on) and optionally fan min on time."""
        if self.read_only:
            return {"success": False, "error": "Read-only mode enabled"}

        valid_modes = ["auto", "on"]
        if fan_mode not in valid_modes:
            return {"success": False, "error": f"Invalid fan mode. Must be one of: {valid_modes}"}

        try:
            settings = {"vent": fan_mode}
            if fan_min_on_time is not None:
                settings["fanMinOnTime"] = fan_min_on_time

            body = {"thermostat": {"settings": settings}}
            self._send_post(body, thermostat_id)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error setting fan mode: {e}")
            return {"success": False, "error": str(e)}

    async def create_vacation(
        self,
        name: str,
        cool_temp: float,
        heat_temp: float,
        start_date: str,
        start_time: str,
        end_date: str,
        end_time: str,
        thermostat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a vacation event."""
        if self.read_only:
            return {"success": False, "error": "Read-only mode enabled"}

        try:
            params = {
                "name": name,
                "coolHoldTemp": int(cool_temp * 10),
                "heatHoldTemp": int(heat_temp * 10),
                "startDate": start_date,
                "startTime": start_time,
                "endDate": end_date,
                "endTime": end_time
            }
            self._send_function("createVacation", params, thermostat_id)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error creating vacation: {e}")
            return {"success": False, "error": str(e)}

    async def delete_vacation(self, name: str, thermostat_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete a vacation event by name."""
        if self.read_only:
            return {"success": False, "error": "Read-only mode enabled"}

        try:
            params = {"name": name}
            self._send_function("deleteVacation", params, thermostat_id)
            return {"success": True}
        except Exception as e:
            logger.error(f"Error deleting vacation: {e}")
            return {"success": False, "error": str(e)}
