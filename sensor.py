from __future__ import annotations

import logging

#home assistant import
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry


#entity import
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback


# local import
from .const import DELAY_TIME, DOMAIN, FANS, TEMPERATURE, WATTSENSOR, TotalWattConsumption
from .RedfishApi import RedfishApihub
from .type_sensor.sensor.SensorCoordinator import SensorCoordinator
from .type_sensor.sensor.Server_Fan_sensor import FanSensor
from .type_sensor.sensor.Server_Power_sensor import ElectricitySensor
from .type_sensor.sensor.Server_Temperature_Sensor import TemperatureSensor



_LOGGER = logging.getLogger(__name__)




async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up entry."""
    api : RedfishApihub = hass.data[DOMAIN][config_entry.entry_id]
    #_LOGGER.info("config_entry: "+str(config_entry.data))
    _LOGGER.info("########### ingresso fan config ############## ")

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

            _LOGGER.info(msg="form Server: "+info['ServiceTag']+"   setup sensor for: "+ EmbSys['id'])
            status = await setup_Embedded_System_Sensor(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)



#    for EmbMan in info["Managers"]:
#        infoSingleSystem['id'] = EmbMan['id']

#        if EmbMan["enable"] is False:

#            _LOGGER.info(msg="form Server: "+info['ServiceTag']+"   setup binary_sensor for: "+ EmbMan['id'])
#            status = await setup_iDrac_Managers_entry(hass= hass, api= api, async_add_entities= async_add_entities, infoSingleSystem= infoSingleSystem)


    return None


async def setup_Embedded_System_Sensor(hass: HomeAssistant, api : RedfishApihub, async_add_entities: AddEntitiesCallback, infoSingleSystem : dict):

    EmbSysInfo = await hass.async_add_executor_job(api.getEmbSysInfo, infoSingleSystem['id'])
    _LOGGER.info(msg="identificativo device: " + str(infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id']) )

    device_info = DeviceInfo(
                #  esempio {('domain', DOMAIN), ('serial', "ServiceTag_Embedded.System.1")}
        identifiers={ (DOMAIN, str(infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id']))  },
        name=EmbSysInfo["name"],
        manufacturer=EmbSysInfo['manufacturer'],
        model=EmbSysInfo['model'],
        sw_version=EmbSysInfo['sw_version'],
        serial_number=str(infoSingleSystem['ServiceTag'])
    )


    EmbSysCooledBy = await hass.async_add_executor_job(api.getEmbeddedSystemCooledBy, infoSingleSystem['id'])
    _LOGGER.info("Cooling components: "+ str(EmbSysCooledBy))

    coordinator = SensorCoordinator(hass, api, infoSingleSystem['id'], infoSingleSystem['PullingTime'])
    #await coordinator.async_config_entry_first_refresh()


    toAddSensor = []

    #add fans sensor
    for elm in EmbSysCooledBy:
        _LOGGER.info("add sensorFan for status: "+elm)
        toAddSensor.append( FanSensor(coordinator,  str({"type": FANS, "id": elm}), device_info, infoSingleSystem) )


    #add Power sensor sensor
    _LOGGER.info("add Power Sensor for status: "+infoSingleSystem['id'])
    toAddSensor.append( ElectricitySensor(coordinator, str({"type": WATTSENSOR, "id": TotalWattConsumption}), device_info, infoSingleSystem) )


    #TODO add temp sensor
    tempSensor = await hass.async_add_executor_job(api.getTemperatureSensor, infoSingleSystem['id'])
    for elm in tempSensor:
        _LOGGER.info("add sensorTemp for status: "+elm.get("Name"))
        toAddSensor.append( TemperatureSensor(coordinator, str({"type": TEMPERATURE, "id": elm.get("Name")}), device_info, infoSingleSystem) )

    #TODO add PSU sensor



    #add sensor
    async_add_entities(toAddSensor,True)
    #schedule first update
    await coordinator.async_config_entry_first_refresh()
    #coordinator.async_update_listeners()



    return True