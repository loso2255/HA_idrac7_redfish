
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
from ...const import SERVER_POWER_STATUS_POOL

_LOGGER = logging.getLogger(__name__)

class PowerStatusCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, my_api : RedfishApihub) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Power Status",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=SERVER_POWER_STATUS_POOL),
        )

        self.my_api = my_api

        return None

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(7):

                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                listening_idx = set(self.async_contexts())
                _LOGGER.info("idx_info: "+str(listening_idx))

                result : dict = {}
                for elm in listening_idx:
                    result[elm] = await self.hass.async_add_executor_job(self.my_api.getpowerState, elm )

                return result

        except InvalidCredentialsError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")





class PowerStatusBinarySensor(CoordinatorEntity,BinarySensorEntity):
    """The iDrac's current power sensor entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, idx, device_info: DeviceInfo, infoSingleSystem : dict) ->None:
        super().__init__(coordinator, context=idx)
        self.idx = idx

        self.entity_description = BinarySensorEntityDescription(
            key='Power Status',
            name='Power Status',
            icon='mdi:power',
            device_class=BinarySensorDeviceClass.RUNNING,
        )

        self._attr_device_info = device_info
        self._attr_unique_id = infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id']+"_status"
        self._attr_has_entity_name = True


    @property
    def name(self):
        """Name of the entity."""
        return self.entity_description.name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.info("coordinator data Power Status: "+str(self.coordinator.data))

        self._attr_is_on = self.coordinator.data[self.idx]["state"]

        if self.coordinator.data[self.idx]["state"] == "On":
            self._attr_is_on = True
        else:
            self._attr_is_on = False

        self.async_write_ha_state()