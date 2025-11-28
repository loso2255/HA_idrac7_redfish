import logging
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.core import callback



from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator


#local import

from ...const import FANS, REQUEST_SENSOR, TEMPERATURE, WATTSENSOR

_LOGGER = logging.getLogger(__name__)


class TemperatureSensor(CoordinatorEntity,SensorEntity):
    """The iDrac's current power sensor entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, idx : str, device_info: DeviceInfo, infoSingleSystem : dict) ->None:
        super().__init__(coordinator, context=idx)

        self.idx = eval(idx)


        self.entity_description = SensorEntityDescription(
            key=self.idx.get("type")+""+self.idx.get("id"),
            name=self.idx.get("id"),
            icon='mdi:thermometer',
            native_unit_of_measurement='°C',
            device_class = SensorDeviceClass.TEMPERATURE,
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

        value = self.coordinator.data.get(TEMPERATURE, {} ).get( self.idx.get("id") )

        if (value == 'None') or (value is None):
            #self._attr_native_value = 0
            self._attr_available = False
        else:
            self._attr_native_value = value


        self.async_write_ha_state()