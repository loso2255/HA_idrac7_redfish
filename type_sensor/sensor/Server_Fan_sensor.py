from datetime import timedelta
import logging
import sys, os
import async_timeout
from homeassistant.components.api import APIErrorLog
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorStateClass
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

_LOGGER = logging.getLogger(__name__)


class FansCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, my_api : RedfishApihub, idDevice : str, PoolingUpdate : int) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Power Status",
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
            async with async_timeout.timeout(7):

                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                listening_idx = set(self.async_contexts())
                _LOGGER.info("idx_info fans: "+str(listening_idx))
                _LOGGER.info("############ sono prima del forrr dele fan ############# ")



                result : dict = {}
                for elm in listening_idx:
                    _LOGGER.info("Sono dentro il ffor delle faNS " + str(elm))

                    #elm = dict("{'idSys': 'System.Embedded.1', 'idFan': '0x17%7C%7CFan.Embedded.6'}")
                    #_LOGGER.info("Sto cercando il dato nuovo della fan id : "+ str(elm.keys))
                    #if result[elm['idSys']] is None:
                    #    result[elm['idSys']] = { elm['idFan'] : await self.hass.async_add_executor_job( self.my_api.getFanSensor, elm['idSys'], elm['idFan'] )}
                    #else:
                    result[elm['idFan']] = await self.hass.async_add_executor_job( self.my_api.getFanSensor, self.id_device, elm['idFan'] )

                _LOGGER.info("############ sono dopo del forrr dele fan ############# ")
                _LOGGER.info("ecco cosa ho recuperato: "+str(result))

                return result

        except InvalidCredentialsError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")



class FanSensor(CoordinatorEntity,SensorEntity):
    """The iDrac's current power sensor entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, idx, device_info: DeviceInfo, infoSingleSystem : dict) ->None:
        super().__init__(coordinator, context=idx)

        self.idx = idx

        self.entity_description = SensorEntityDescription(
            key='Fan Speed Rpm',
            name='Fan Speed Rpm',
            icon='mdi:fan',
            native_unit_of_measurement='RPM',
            state_class=SensorStateClass.MEASUREMENT
            #device_class=SensorDeviceClass.,
        )

        self.id_fan = infoSingleSystem['idFan']

        self._attr_device_info = device_info
        self._attr_unique_id = infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id']+"_"+infoSingleSystem['idFan']
        self._attr_has_entity_name = True

        #coordinator._schedule_refresh()


    @property
    def name(self):
        """Name of the entity."""
        return self.entity_description.name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.info("coordinator data Fans Status: "+str(self.coordinator.data))

        self._attr_native_value = self.coordinator.data[self.id_fan]
        self.async_write_ha_state()