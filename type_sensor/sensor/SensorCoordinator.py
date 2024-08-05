import asyncio
from datetime import timedelta
import logging
import async_timeout

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

from ...const import FANS, REQUEST_FOR_ELECTRICITY_SENSOR, REQUEST_FOR_FAN_SPEED, InletTemp, TotalWattConsumption
from ...RedfishApi import RedfishApihub

_LOGGER = logging.getLogger(__name__)

class SensorCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, my_api : RedfishApihub, idDevice : str, PoolingUpdate : int) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Fans Speed",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=int(PoolingUpdate)) #timedelta(seconds=5),
        )

        self.id_device = idDevice
        self.my_api = my_api

        return None

    async def _async_update_data(self):
        try:

            listening_idx = set(self.async_contexts())
            _LOGGER.info("entitys registered for fan speed: "+str(listening_idx))




            result : dict = {}
            for elm in listening_idx:
                elm = eval(elm)

                # reading "FANS" sensor type
                if elm.get("type") == FANS:
                    try:
                        async with async_timeout.timeout(REQUEST_FOR_FAN_SPEED):

                            _LOGGER.info(msg="reading value of FAN: "+elm.get("id"))
                            funSpeed = await self.hass.async_add_executor_job( self.my_api.getFanSensor,  str(self.id_device), str(elm.get("id"))  )

                            if funSpeed is None:
                                result[elm.get("id")] = None
                            else:
                                result[elm.get("id")] = funSpeed


                    except (RuntimeError, asyncio.TimeoutError) as err:
                        _LOGGER.info(msg="Fallied update Fan Sensor: "+elm.get("id"))

                # reading "FANS" sensor type
                elif elm.get("type") == TotalWattConsumption:
                    try:
                        async with async_timeout.timeout(REQUEST_FOR_ELECTRICITY_SENSOR):

                            _LOGGER.info(msg="reading value of CONSUMPTION: "+elm.get("id"))
                            resServer = await self.hass.async_add_executor_job( self.my_api.getElectricitySensor,  str(self.id_device)  )

                            if resServer is None:
                                result[elm.get("id")] = None
                            else:
                                result[elm.get("id")] = resServer


                    except (RuntimeError, asyncio.TimeoutError) as err:
                        _LOGGER.info(msg="Fallied update Fan Sensor: "+elm.get("id"))

                #TODO reading "Temp" sensor type


                #TODO reading "PSU" voltage Sensor



            _LOGGER.info("ecco cosa ho recuperato: "+str(result))
            return result

        except InvalidCredentialsError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")