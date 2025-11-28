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

from datetime import timedelta




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
    for EmbSys in info["Members"]:
        infoSingleSystem['id'] = EmbSys['id']

        if EmbSys["enable"] is True:

        infoSingleSystem['id'] = EmbSys['id']
        _LOGGER.info("form Server: %s   setup button for: %s", service_tag, EmbSys['id'])
        await setup_Embedded_System_entry(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)



#    for EmbMan in info["Managers"]:
#        infoSingleSystem['id'] = EmbMan['id']

#        if EmbMan["enable"] is False:

#            _LOGGER.info(msg="form Server: "+info['ServiceTag']+"   setup binary_sensor for: "+ EmbMan['id'])
#            status = await setup_iDrac_Managers_entry(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)


    return None


async def setup_Embedded_System_entry(hass: HomeAssistant, api : RedfishApihub, async_add_entities: AddEntitiesCallback, infoSingleSystem : dict):

    EmbSysInfo = await hass.async_add_executor_job(api.getEmbSysInfo, infoSingleSystem['id'])
    device_info = DeviceInfo(
                #  esempio {('domain', DOMAIN), ('serial', "ServiceTag_Embedded.System.1")}
        identifiers={ (DOMAIN, str(infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id'])) },
        name=EmbSysInfo["name"],
        manufacturer=EmbSysInfo['manufacturer'],
        model=EmbSysInfo['model'],
        sw_version=EmbSysInfo['sw_version'],
        serial_number=str(infoSingleSystem['ServiceTag'])
    )


    EmbSysPowerActions = await hass.async_add_executor_job(api.getEmbSysPowerActions, infoSingleSystem['id'])
    _LOGGER.info("supported power functions:" + str(EmbSysPowerActions))


    powerButtonList = []
    for elm in EmbSysPowerActions:
        _LOGGER.info("add power button for status: "+elm)

        if elm != "Nmi":
            infoSingleSystem['powerActions'] = elm
            powerButtonList.append( ServerPowerButton(hass=hass, api = api, device_info= device_info, infoSingleSystem= infoSingleSystem) )


    async_add_entities(powerButtonList,True)


    return True

