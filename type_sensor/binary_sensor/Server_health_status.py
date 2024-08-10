
import asyncio
from datetime import timedelta
import logging
import sys, os
import async_timeout
from homeassistant.components.api import APIErrorLog
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed

from redfish.rest.v1 import (
    InvalidCredentialsError,
    RetriesExhaustedError,
    ServerDownOrUnreachableError,
    SessionCreationError,
)

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator, UpdateFailed


#local import

from ...RedfishApi import RedfishApihub
from ...const import REQUEST_FOR_STATUS_HEALTH

_LOGGER = logging.getLogger(__name__)

class HealthStatusCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, my_api : RedfishApihub, PoolingUpdate : int) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Health Status",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval= timedelta(seconds=int(PoolingUpdate)) #timedelta(seconds=5)
        )

        self.my_api = my_api

        return None

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                listening_idx = set(self.async_contexts())
                _LOGGER.info("idx_info: "+str(listening_idx))

                result : dict = {}
                for elm in listening_idx:
                    # Note: asyncio.TimeoutError and aiohttp.ClientError are already
                    # handled by the data update coordinator.
                    async with async_timeout.timeout(REQUEST_FOR_STATUS_HEALTH):
                        result[elm] = await self.hass.async_add_executor_job(self.my_api.getHealthStatus, elm )

                return result

        except InvalidCredentialsError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err

        except (RuntimeError, asyncio.TimeoutError) as err:
            _LOGGER.error(msg="Timeout update Sensor General Health sensor")
            raise UpdateFailed(f"Timeout update Sensor General Health sensor: {err}")



        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")





class HealthStatusBinarySensor(CoordinatorEntity,BinarySensorEntity):
    """The iDrac's current power sensor entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, idx, device_info: DeviceInfo, infoSingleSystem : dict) ->None:
        super().__init__(coordinator, context=idx)
        self.idx = idx

        self.entity_description = BinarySensorEntityDescription(
            key='Health Status',
            name='Health Status',
            icon='mdi:check-circle',
            device_class=BinarySensorDeviceClass.PROBLEM,
        )

        self._attr_device_info = device_info
        self._attr_unique_id = infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id']+"_Health"
        self._attr_has_entity_name = True


    @property
    def name(self):
        """Name of the entity."""
        return self.entity_description.name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.info("coordinator data Health: "+str(self.coordinator.data))

        value = self.coordinator.data

        if value is not None:
            if value.get(self.idx,{}).get("health") == 'OK':
                self._attr_is_on = False
            else:
                self._attr_is_on = True

        else:
            self._attr_is_on = True

        self.async_write_ha_state()