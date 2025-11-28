"""Data update coordinator for iDRAC Redfish integration."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_manager import ApiRequestManager
from .const import (
    DOMAIN,
    PRIORITY_HIGH,
    PRIORITY_NORMAL,
    REQUEST_FOR_STATUS_HEALTH,
    REQUEST_FOR_STATUS_POWER,
    REQUEST_SENSOR,
    UPDATE_INTERVAL_FAST,
    UPDATE_INTERVAL_NORMAL,
)

_LOGGER = logging.getLogger(__name__)


class IdracSystemCoordinator(DataUpdateCoordinator):
    """Coordinator for system status (power, health)."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api_manager: ApiRequestManager,
        client: Any,  # Replace with your actual client type
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_system",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_FAST),
            config_entry=config_entry,
        )
        self.api_manager = api_manager
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch system status data."""
        try:
            # Use API manager for coordinated requests
            power_status = await self.api_manager.request(
                self.client.get_power_status,
                priority=PRIORITY_HIGH,
                timeout=REQUEST_FOR_STATUS_POWER,
            )

            health_status = await self.api_manager.request(
                self.client.get_health_status,
                priority=PRIORITY_HIGH,
                timeout=REQUEST_FOR_STATUS_HEALTH,
            )

            return {
                "power": power_status,
                "health": health_status,
            }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with iDRAC: {err}") from err


class IdracSensorCoordinator(DataUpdateCoordinator):
    """Coordinator for sensor data (temperature, fans, PSU)."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api_manager: ApiRequestManager,
        client: Any,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_sensors",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_NORMAL),
            config_entry=config_entry,
        )
        self.api_manager = api_manager
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch sensor data."""
        try:
            # Batch multiple sensor requests
            requests = [
                (self.client.get_temperature_sensors, (), {}),
                (self.client.get_fan_sensors, (), {}),
                (self.client.get_psu_sensors, (), {}),
                (self.client.get_power_consumption, (), {}),
            ]

            results = await self.api_manager.batch_request(
                requests,
                timeout=REQUEST_SENSOR,
            )

            # Check for exceptions in results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    _LOGGER.warning("Sensor request %d failed: %s", i, result)

            return {
                "temperature": results[0] if not isinstance(results[0], Exception) else None,
                "fans": results[1] if not isinstance(results[1], Exception) else None,
                "psu": results[2] if not isinstance(results[2], Exception) else None,
                "power": results[3] if not isinstance(results[3], Exception) else None,
            }
        except Exception as err:
            raise UpdateFailed(f"Error fetching sensor data: {err}") from err
