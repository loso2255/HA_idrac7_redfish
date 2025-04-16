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
    """Set up binary sensors from a config entry."""
    api: RedfishApihub = hass.data[DOMAIN][config_entry.entry_id]

    # Get embedded systems and their status from config_entry data
    config_data = config_entry.data
    service_tag = config_data["info"]["ServiceTag"]
    pulling_time = config_data["authdata"][DELAY_TIME]
    embedded_systems = config_data["info"]["Members"]

    _LOGGER.debug("Setting up binary sensors for iDRAC %s", service_tag)

    # Prepare base info for each system
    info_single_system: dict = {
        "ServiceTag": service_tag,
        "PullingTime": pulling_time
    }

    # Set up sensors for each enabled embedded system
    for emb_sys in embedded_systems:
        # Skip disabled embedded systems
        if not emb_sys.get("enable", False):
            _LOGGER.info("Skipping disabled system: %s", emb_sys["id"])
            continue

        # Set up binary sensors for this embedded system
        info_single_system["id"] = emb_sys["id"]
        _LOGGER.debug("Setting up binary sensors for system: %s", emb_sys["id"])

        await setup_Embedded_System_entry(
            hass=hass,
            api=api,
            async_add_entities=async_add_entities,
            infoSingleSystem=info_single_system.copy()
        )

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