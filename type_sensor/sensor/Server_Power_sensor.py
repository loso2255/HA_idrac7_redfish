from datetime import timedelta
import logging
import sys, os
import async_timeout
from homeassistant.components.api import APIErrorLog
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
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

from ...const import REQUEST_FOR_ELECTRICITY_SENSOR
from ...RedfishApi import RedfishApihub

_LOGGER = logging.getLogger(__name__)


class ElectricityCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, my_api : RedfishApihub, idDevice : str, PoolingUpdate : int) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Electricity Coordinator",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=int(PoolingUpdate)) #timedelta(seconds=5),
        )

        self.id_device = idDevice
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
            async with async_timeout.timeout(REQUEST_FOR_ELECTRICITY_SENSOR):

                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                listening_idx = set(self.async_contexts())
                _LOGGER.info("entitys registered for PowerConsumtion: "+str(listening_idx))

                resServer = await self.hass.async_add_executor_job( self.my_api.getElectricitySensor,  str(self.id_device)  )

                #_LOGGER.info("ecco cosa ho recuperato PowerConsumtion: "+str(resServer))

                return resServer

        except InvalidCredentialsError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")



class ElectricitySensor(CoordinatorEntity,SensorEntity):
    """The iDrac's current power sensor entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, idx : str, device_info: DeviceInfo, infoSingleSystem : dict) ->None:
        super().__init__(coordinator, context=idx)

        self.idx = idx


        self.entity_description = SensorEntityDescription(
            key=idx,
            name=idx,
            icon='mdi:lightning-bolt',
            native_unit_of_measurement='W',
            device_class = SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT
        )

        self.id_fan = idx

        self._attr_device_info = device_info
        self._attr_unique_id = infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id']+"_"+idx
        self._attr_has_entity_name = True

        #coordinator._schedule_refresh()


    @property
    def name(self):
        """Name of the entity."""
        return self.entity_description.name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.info("update the info of the fan: "+self.idx)

        value = self.coordinator.data.get(self.idx)
        if value is None:
            self._attr_native_value = 0
        else:
            self._attr_native_value = value


        self.async_write_ha_state()