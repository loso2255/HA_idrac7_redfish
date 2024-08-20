import logging
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.core import callback

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator


#local impor

from ...const import WATTSENSOR

_LOGGER = logging.getLogger(__name__)


class ElectricitySensor(CoordinatorEntity,SensorEntity):
    """The iDrac's current power sensor entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, idx : str, device_info: DeviceInfo, infoSingleSystem : dict) ->None:
        super().__init__(coordinator, context=idx)

        self.idx = eval(idx)


        self.entity_description = SensorEntityDescription(
            key=self.idx.get("type")+""+self.idx.get("id"),
            name="PowerConsumedWatts",
            icon='mdi:lightning-bolt',
            native_unit_of_measurement='W',
            device_class = SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT
        )


        self._attr_device_info = device_info
        self._attr_unique_id = infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id']+"_"+self.idx.get("id")
        self._attr_has_entity_name = True

        #coordinator._schedule_refresh()


    @property
    def name(self):
        """Name of the entity."""
        return self.entity_description.name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        #_LOGGER.info("update the info of the power: "+self.idx.get("id"))
        #_LOGGER.info("get the info of coordinator: "+str(self.coordinator.data))

        value = self.coordinator.data.get(WATTSENSOR, {} ).get( self.idx.get("id") )
        if (value == 'None') or (value is None):
            self._attr_native_value = 0
        else:
            self._attr_native_value = value


        self.async_write_ha_state()