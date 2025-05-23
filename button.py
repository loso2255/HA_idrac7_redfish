from __future__ import annotations

import logging

#home assistant import

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

#platoform import
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass, \
    BinarySensorEntityDescription

#entity import
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_DELAY

from redfish.rest.v1 import (
    InvalidCredentialsError,
    RetriesExhaustedError,
    ServerDownOrUnreachableError,
    SessionCreationError,
)


# local import
from .const import DELAY_TIME, DOMAIN
from .RedfishApi import RedfishApihub
from .type_sensor.button.Server_power_button import ServerPowerButton

_LOGGER = logging.getLogger(__name__)

from datetime import timedelta




async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up entry."""
    api : RedfishApihub = hass.data[DOMAIN][config_entry.entry_id]
    #_LOGGER.info("config_entry: "+str(config_entry.data))

    # topology info test connections
    info = await hass.async_add_executor_job(api.getRedfishInfo)


    infoSingleSystem : dict = {}
    infoSingleSystem['ServiceTag'] = info['ServiceTag']
    infoSingleSystem['PullingTime'] = config_entry.data["authdata"][DELAY_TIME]

    # nel for, per ogni embbeddded system get System.Embedded.info
    # setto i sensori dell'embedded system
    for EmbSys in info["Members"]:
        infoSingleSystem['id'] = EmbSys['id']

        if EmbSys["enable"] is True:

            _LOGGER.info(msg="form Server: "+info['ServiceTag']+"   setup button for: "+ EmbSys['id'])
            status = await setup_Embedded_System_entry(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)



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

