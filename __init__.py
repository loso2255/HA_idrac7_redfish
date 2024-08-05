"""The HA_iidrac7_redfish integration."""
from __future__ import annotations
import logging

from redfish.rest.v1 import (
    InvalidCredentialsError,
    RetriesExhaustedError,
    ServerDownOrUnreachableError,
    SessionCreationError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .RedfishApi import RedfishApihub
from .const import DOMAIN

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA_idrac7_redfish from a config entry."""
    _LOGGER.info(msg="#################ATTENZIONE ENTRATA INIT SECTIONS############################")


    hass.data.setdefault(DOMAIN, {})
    #1. Create API instance
    #_LOGGER.info(msg="qualche info in piu entry config:"+str(entry))
    #_LOGGER.info(msg="qualche info in piu entry config:"+str(entry.data))

    api = RedfishApihub(ip=entry.data["authdata"][CONF_HOST],user=entry.data["authdata"][CONF_USERNAME],password=entry.data["authdata"][CONF_PASSWORD])

    #2. Validate the API connection
    try:
        ActualServiceTag  = await hass.async_add_executor_job(api.getServiceTag)

    except RetriesExhaustedError:
        _LOGGER.error(msg="name server: ["+ entry.data["info"]["ServiceTag"]+ "] Retries Exhausted: maybe the server is unreachable")
        raise ConfigEntryNotReady("Connection error while connecting to: "+entry.data["info"]["ServiceTag"])

    except Exception as exp:
        _LOGGER.exception(msg="name server: [" + entry.data["info"]["ServiceTag"] + "]" + str(exp))
        raise ConfigEntryNotReady("name server: [" + entry.data["info"]["ServiceTag"] + "] not knowing error")


    else:
        #connection valid check service tag
        if ActualServiceTag != entry.data["info"]["ServiceTag"]:
            _LOGGER.error(msg="error not excepted service tag")

            await hass.async_add_executor_job(api.__del__)
            raise ConfigEntryNotReady("error not excepted service tag")

        else:
            #check credentials and session creation
            try:
                await hass.async_add_executor_job(api.singleton_login)

                #3. Store an API object for your platforms to access
                # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

                _LOGGER.info(msg="#### controllo singleton login successo ######")
                #Store an API object
                hass.data[DOMAIN][entry.entry_id] = api

                #sensori di health e power status
                await hass.async_create_task(
                    hass.config_entries.async_forward_entry_setups(
                        entry, Platform.BINARY_SENSOR
                    )
                )

                # bottoni di power effect
                await hass.async_create_task(
                    hass.config_entries.async_forward_entry_setups(
                        entry, Platform.BUTTON
                    )
                )

                # sensori di temp, fans, ecc..
                await hass.async_create_task(
                    hass.config_entries.async_forward_entry_setups(
                        entry, Platform.SENSOR
                    )
                )

            except SessionCreationError:
                _LOGGER.exception( msg="name server: [" + entry.data["info"]["ServiceTag"] + "] Session Creation Error")
                raise ConfigEntryNotReady("name server: [" + entry.data["info"]["ServiceTag"] + "] Session Creation Error")

            except InvalidCredentialsError:
                _LOGGER.exception( msg="name server: [" + entry.data["info"]["ServiceTag"] + "] invalid_auth")
                raise ConfigEntryNotReady("name server: [" + entry.data["info"]["ServiceTag"] + "] invalid_auth")

            except RetriesExhaustedError:
                _LOGGER.error(msg="name server: ["+ entry.data["info"]["ServiceTag"]+ "] Retries Exhausted: maybe the server is unreachable")
                raise ConfigEntryNotReady("Connection error while connecting to: "+entry.data["info"]["ServiceTag"])

            except Exception as exp:
                _LOGGER.exception(msg="name server: [" + entry.data["info"]["ServiceTag"] + "]" + str(exp))
                raise ConfigEntryNotReady("name server: [" + entry.data["info"]["ServiceTag"] + "] Generic Exception")



    return True





async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok_BinarySensor = await hass.config_entries.async_unload_platforms(entry, [ Platform.BINARY_SENSOR, Platform.SENSOR, Platform.BUTTON  ])

    if unload_ok_BinarySensor:
        api : RedfishApi = hass.data[DOMAIN].pop(entry.entry_id)
        try:
            await hass.async_add_executor_job(api.__del__)

        except Exception as err:
            _LOGGER.error(msg="can't contact the server on unload entry "+ err)

    return unload_ok_BinarySensor
