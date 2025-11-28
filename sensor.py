from __future__ import annotations

import logging

#home assistant import
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry


#entity import
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback


# local import
from .const import DELAY_TIME, DOMAIN, FANS, PSU, TEMPERATURE, WATTSENSOR, TotalWattConsumption
from .RedfishApi import RedfishApihub
from .type_sensor.sensor.SensorCoordinator import SensorCoordinator
from .type_sensor.sensor.Server_Fan_sensor import FanSensor
from .type_sensor.sensor.Server_Power_sensor import ElectricitySensor
from .type_sensor.sensor.Server_PSU_sensor import PSUSensor
from .type_sensor.sensor.Server_Temperature_Sensor import TemperatureSensor



_LOGGER = logging.getLogger(__name__)




async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up sensors from a config entry."""
    api: RedfishApihub = hass.data[DOMAIN][config_entry.entry_id]

    # Get embedded systems and their status from config_entry data
    config_data = config_entry.data
    service_tag = config_data["info"]["ServiceTag"]
    pulling_time = config_data["authdata"][DELAY_TIME]
    embedded_systems = config_data["info"]["Members"]

    _LOGGER.debug("Setting up sensors for iDRAC %s", service_tag)

    # Prepare base info for each system
    info_single_system: dict = {
        "ServiceTag": service_tag,
        "PullingTime": pulling_time
    }

    # Set up sensors for each enabled embedded system
    for emb_sys in embedded_systems:
        # Skip disabled embedded systems
        if not emb_sys.get("enable", True):
            _LOGGER.debug("Skipping disabled system: %s", emb_sys["id"])
            continue

        info_single_system["id"] = emb_sys["id"]
        _LOGGER.debug("Setting up sensors for system: %s", emb_sys["id"])

        await setup_Embedded_System_entry(
            hass=hass,
            api=api,
            async_add_entities=async_add_entities,
            infoSingleSystem=info_single_system.copy()
        )
        # Set up sensors for this embedded system



    # For future implementation: Manager sensors
    # managers = config_data["info"]["Managers"]
    # for manager in managers:
    #     if manager.get("enable", False):
    #         info_single_system["id"] = manager["id"]
    #         await setup_iDrac_Managers_entry(
    #             hass=hass,
    #             api=api,
    #             async_add_entities=async_add_entities,
    #             infoSingleSystem=info_single_system.copy()
    #         )

    return None


async def setup_Embedded_System_entry(hass: HomeAssistant, api : RedfishApihub, async_add_entities: AddEntitiesCallback, infoSingleSystem : dict):
    """Set up sensors for an embedded system."""
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

    coordinator = SensorCoordinator(hass, api, infoSingleSystem['id'], infoSingleSystem['PullingTime'])

    EmbSysCooledBy = await hass.async_add_executor_job(api.getEmbeddedSystemCooledBy, infoSingleSystem['id'])
    _LOGGER.info("Cooling components: "+ str(EmbSysCooledBy))

    toAddSensor = []

    #add fans sensor
    for elm in EmbSysCooledBy:
        _LOGGER.info("add sensorFan for status: "+elm)
        toAddSensor.append( FanSensor(coordinator,  str({"type": FANS, "id": elm}), device_info, infoSingleSystem) )


    #add Power sensor sensor
    _LOGGER.info("add Power Sensor for status: "+infoSingleSystem['id'])
    toAddSensor.append( ElectricitySensor(coordinator, str({"type": WATTSENSOR, "id": TotalWattConsumption}), device_info, infoSingleSystem) )


    #add temp sensor
    tempSensor = await hass.async_add_executor_job(api.getTemperatureSensor, infoSingleSystem['id'])
    for elm in tempSensor:
        _LOGGER.info("add sensorTemp for status: "+elm.get("Name"))
        toAddSensor.append( TemperatureSensor(coordinator, str({"type": TEMPERATURE, "id": elm.get("Name")}), device_info, infoSingleSystem) )

    #add PSU voltage sensor
    EmbSysPoweredBy = await hass.async_add_executor_job(api.getEmbeddedSystemPoweredBy, infoSingleSystem['id'])
    _LOGGER.info("Power supply units: "+ str(EmbSysPoweredBy))
    for psuID in EmbSysPoweredBy:
        _LOGGER.info("add PSU voltage sensor for: "+psuID)
        toAddSensor.append( PSUSensor(coordinator, str({"type": PSU, "id": psuID}), device_info, infoSingleSystem) )

    #add sensor
    async_add_entities(toAddSensor,True)
    #schedule first update
    await coordinator.async_config_entry_first_refresh()

    return True


#setup entry for iDrac Managers
async def setup_iDrac_Managers_entry(hass: HomeAssistant, api : RedfishApihub, async_add_entities: AddEntitiesCallback, infoSingleSystem : dict):
    """Set up sensors for an iDRAC manager."""
    return True