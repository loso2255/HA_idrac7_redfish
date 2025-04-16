"""Integration for Dell iDRAC Redfish interface."""
from __future__ import annotations

import logging

#homeassistant import
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD

#local import
from .const import DOMAIN, DELAY_TIME
from .RedfishApi import RedfishApihub


_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Dell iDRAC Redfish from a config entry."""
    api_data = {}
    api_data = config_entry.data["authdata"]
    host = api_data.get(CONF_HOST, "")
    username = api_data.get(CONF_USERNAME, "")
    password = api_data.get(CONF_PASSWORD, "")

    try:
        api = RedfishApihub(host, username, password)

        # Validate connection
        await hass.async_add_executor_job(api.getRedfishInfo)
    except Exception as e:
        _LOGGER.error("Failed to connect to iDRAC host %s: %s", host, e)
        raise ConfigEntryNotReady(f"Failed to connect to iDRAC: {e}") from e

    # Store API instance for platforms to access
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = api

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Register update listener for config entry changes
    config_entry.async_on_unload(config_entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        # Clean up iDRAC connection
        api = hass.data[DOMAIN].pop(config_entry.entry_id)
        await hass.async_add_executor_job(api.__del__)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload a config entry when its data changes."""
    _LOGGER.debug("Reloading iDRAC %s due to config changes", config_entry.data["info"]["ServiceTag"])
    await async_unload_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)
