from __future__ import annotations

import logging

#home assistant import
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

#entity import
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# local import
from .const import DELAY_TIME, DOMAIN
from .RedfishApi import RedfishApihub
from .type_sensor.button.Server_power_button import ServerPowerButton

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up entry."""
    api : RedfishApihub = hass.data[DOMAIN][config_entry.entry_id]

    # Get embedded systems and their status from config_entry data
    config_data = config_entry.data
    service_tag = config_data["info"]["ServiceTag"]
    pulling_time = config_data["authdata"][DELAY_TIME]
    embedded_systems = config_data["info"]["Members"]

    _LOGGER.debug("Setting up buttons for iDRAC %s", service_tag)

    # Prepare base info for each system
    infoSingleSystem : dict = {
        "ServiceTag": service_tag,
        "PullingTime": pulling_time
    }

    # nel for, per ogni embbeddded system get System.Embedded.info
    # setto i sensori dell'embedded system
    for EmbSys in embedded_systems:
        # Skip disabled embedded systems
        if not EmbSys.get("enable", True):
            _LOGGER.debug("Skipping disabled system: %s", EmbSys['id'])
            continue

        infoSingleSystem['id'] = EmbSys['id']
        _LOGGER.info("form Server: %s   setup button for: %s", service_tag, EmbSys['id'])
        await setup_Embedded_System_entry(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)



#    for EmbMan in info["Managers"]:
#        infoSingleSystem['id'] = EmbMan['id']

#        if EmbMan["enable"] is False:

#            _LOGGER.info(msg="form Server: "+info['ServiceTag']+"   setup binary_sensor for: "+ EmbMan['id'])
#            status = await setup_iDrac_Managers_entry(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)


    return None


async def setup_Embedded_System_entry(hass: HomeAssistant, api: RedfishApihub, async_add_entities: AddEntitiesCallback, infoSingleSystem: dict):
    """Set up button entities for an embedded system."""
    EmbSysInfo = await hass.async_add_executor_job(api.getEmbSysInfo, infoSingleSystem['id'])
    _LOGGER.info("Setting up buttons for device: %s_%s", infoSingleSystem['ServiceTag'], infoSingleSystem['id'])

    device_info = DeviceInfo(
        identifiers={(DOMAIN, f"{infoSingleSystem['ServiceTag']}_{infoSingleSystem['id']}")},
        name=EmbSysInfo["name"],
        manufacturer=EmbSysInfo['manufacturer'],
        model=EmbSysInfo['model'],
        sw_version=EmbSysInfo['sw_version'],
        serial_number=infoSingleSystem['ServiceTag']
    )

    EmbSysPowerActions = await hass.async_add_executor_job(api.getEmbSysPowerActions, infoSingleSystem['id'])
    _LOGGER.info("Supported power functions: %s", EmbSysPowerActions)

    power_button_list = []
    for elm in EmbSysPowerActions:
        if elm != "Nmi":  # Skip Non-Maskable Interrupt
            _LOGGER.info("Adding power button for action: %s", elm)
            info = dict(infoSingleSystem)
            info['powerActions'] = elm
            power_button_list.append(ServerPowerButton(
                hass=hass,
                api=api,
                device_info=device_info,
                infoSingleSystem=info
            ))

    async_add_entities(power_button_list, True)
    return True

