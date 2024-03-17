from __future__ import annotations

import logging

#home assistant import
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

#platoform import
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass, \
    BinarySensorEntityDescription

#entity import
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback


# local import
from .const import DOMAIN
from .RedfishApi import RedfishApihub
from .type_sensor.binary_sensor.Server_status import IdracStatusBinarySensor,StatusCoordinator

_LOGGER = logging.getLogger(__name__)

from datetime import timedelta

SCAN_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up entry."""
    api : RedfishApihub = hass.data[DOMAIN][config_entry.entry_id]

    # topology info TODO test connections
    info = await hass.async_add_executor_job(api.getRedfishInfo)

    infoSingleSystem : dict = {}
    infoSingleSystem['ServiceTag'] = info['ServiceTag']

    # nel for, per ogni embbeddded system get System.Embedded.info
    # setto i sensori dell'embedded system
    for EmbSys in info["Members"]:
        infoSingleSystem['id'] = EmbSys['id']

        if EmbSys["enable"] is False:

            _LOGGER.info(msg="form Server: "+info['ServiceTag']+"   setup binary_sensor for: "+ EmbSys['id'])
            status = await setup_Embedded_System_entry(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)



    for EmbMan in info["Managers"]:
        infoSingleSystem['id'] = EmbMan['id']

        if EmbMan["enable"] is False:

            _LOGGER.info(msg="form Server: "+info['ServiceTag']+"   setup binary_sensor for: "+ EmbMan['id'])
            status = await setup_iDrac_Managers_entry(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)



    return None







#TODO setup entry for Embedded System
async def setup_Embedded_System_entry(hass: HomeAssistant, api : RedfishApihub, async_add_entities: AddEntitiesCallback, infoSingleSystem : dict):

    EmbSysInfo = await hass.async_add_executor_job(api.getEmbSysInfo, infoSingleSystem['id'])
    device_info = DeviceInfo(
                #  esempio {('domain', DOMAIN), ('serial', "ServiceTag_Embedded.System.1")}
        identifiers={('domain', DOMAIN), ('serial', str(infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id'])) },
        name=EmbSysInfo["name"],
        manufacturer=EmbSysInfo['manufacturer'],
        model=EmbSysInfo['model'],
        sw_version=EmbSysInfo['sw_version'],
        #serial_number=serial
    )

    coordinator = StatusCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            IdracStatusBinarySensor(coordinator, infoSingleSystem['id'], device_info, infoSingleSystem)
    ],True)


    return True


#TODO setup entry for iDrac Managers
async def setup_iDrac_Managers_entry(hass: HomeAssistant, api : RedfishApihub, async_add_entities: AddEntitiesCallback, infoSingleSystem : dict):




    return True