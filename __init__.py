"""The HA_iidrac7_redfish integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .RedfishApi import RedfishApihub
from .const import DOMAIN

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA_idrac7_redfish from a config entry."""
    _LOGGER.info(msg="#################ATTENZIONE ENTRATA INIT SECTIONS############################")


    hass.data.setdefault(DOMAIN, {})
    # TODO 1. Create API instance
    _LOGGER.info(msg="qualche info in piu entry config:"+str(entry))
    _LOGGER.info(msg="qualche info in piu entry config:"+str(entry.data))

    api = RedfishApihub(ip=entry.data["authdata"][CONF_HOST],user=entry.data["authdata"][CONF_USERNAME],password=entry.data["authdata"][CONF_PASSWORD])

    # TODO 2. Validate the API connection (and authentication)
    ActualServiceTag  = await hass.async_add_executor_job(api.getServiceTag)
    if ActualServiceTag != entry.data["info"]["ServiceTag"]:
        _LOGGER.error(msg="error not excepted service tag")

        await hass.async_add_executor_job(api.__del__)
        return False

    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    hass.data[DOMAIN][entry.entry_id] = api

    #hass.async_create_task(
    #    hass.config_entries.async_forward_entry_setup(
    #        entry, Platform.BINARY_SENSOR
    #    )
    #)



    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
