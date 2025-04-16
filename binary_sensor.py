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
from .type_sensor.binary_sensor.Server_Power_status import PowerStatusBinarySensor,PowerStatusCoordinator
from .type_sensor.binary_sensor.Server_health_status import HealthStatusBinarySensor, HealthStatusCoordinator



_LOGGER = logging.getLogger(__name__)


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

        if EmbSys["enable"] is False:

            _LOGGER.info(msg="form Server: "+info['ServiceTag']+"   setup binary_sensor for: "+ EmbSys['id'])
            status = await setup_Embedded_System_entry(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)



#    for EmbMan in info["Managers"]:
#        infoSingleSystem['id'] = EmbMan['id']

#        if EmbMan["enable"] is False:

#            _LOGGER.info(msg="form Server: "+info['ServiceTag']+"   setup binary_sensor for: "+ EmbMan['id'])
#            status = await setup_iDrac_Managers_entry(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)


    return None


#setup entry for Embedded System
async def setup_Embedded_System_entry(hass: HomeAssistant, api : RedfishApihub, async_add_entities: AddEntitiesCallback, infoSingleSystem : dict):
    """Set up binary sensors for an embedded system."""
    EmbSysInfo = await hass.async_add_executor_job(api.getEmbSysInfo, infoSingleSystem['id'])
    _LOGGER.debug("Setting up device: %s_%s", infoSingleSystem['ServiceTag'], infoSingleSystem['id'])

    device_info = DeviceInfo(
        identifiers={(DOMAIN, f"{infoSingleSystem['ServiceTag']}_{infoSingleSystem['id']}")},
        name=EmbSysInfo["name"],
        manufacturer=EmbSysInfo['manufacturer'],
        model=EmbSysInfo['model'],
        sw_version=EmbSysInfo['sw_version'],
        serial_number=infoSingleSystem['ServiceTag']
    )

    coordinator = PowerStatusCoordinator(hass, api)
    coordinator2 = HealthStatusCoordinator(hass, api, infoSingleSystem['PullingTime'])

    async_add_entities(
        [
            PowerStatusBinarySensor(coordinator, infoSingleSystem['id'], device_info, infoSingleSystem),
            HealthStatusBinarySensor(coordinator2, infoSingleSystem['id'], device_info, infoSingleSystem)
        ],
        True
    )

    await coordinator.async_config_entry_first_refresh()
    await coordinator2.async_config_entry_first_refresh()

    return True


#setup entry for iDrac Managers
async def setup_iDrac_Managers_entry(hass: HomeAssistant, api : RedfishApihub, async_add_entities: AddEntitiesCallback, infoSingleSystem : dict):
    """Set up binary sensors for an iDRAC manager."""
    EmbSysInfo = await hass.async_add_executor_job(api.getEmbeddedManagers, infoSingleSystem['id'])
    device_info = DeviceInfo(
        identifiers={(DOMAIN, f"{infoSingleSystem['ServiceTag']}_{infoSingleSystem['id']}")},
        name=EmbSysInfo["name"],
        #manufacturer=EmbSysInfo['manufacturer'],
        #model=EmbSysInfo['model'],
        sw_version=EmbSysInfo['sw_version'],
        #serial_number=serial
    )

    return True