import logging
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.core import callback

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator


#local import

from ...const import FANS

_LOGGER = logging.getLogger(__name__)


class FanSensor(CoordinatorEntity,SensorEntity):
    """The iDrac's current Fan sensor entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, idx : dict, device_info: DeviceInfo, infoSingleSystem : dict) ->None:

        super().__init__(coordinator, context=idx)

        self.idx = eval(idx)

        getNFan = self.idx.get("id").split(".")
        getNFan = getNFan[len(getNFan)-1]


        self.entity_description = SensorEntityDescription(
            key='Fan Speed '+getNFan,
            name='Fan Speed '+getNFan,
            icon='mdi:fan',
            native_unit_of_measurement='RPM',
            state_class=SensorStateClass.MEASUREMENT
        )

        self.id_fan = idx

        self._attr_device_info = device_info
        self._attr_unique_id = infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id']+"_"+idx
        self._attr_has_entity_name = True

        #coordinator._schedule_refresh()


    @property
    def name(self):
        """Name of the entity."""
        return self.entity_description.name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        #_LOGGER.info("update the info of the fan: "+self.idx.get("id"))
        #_LOGGER.info("coordinator data Fans Status: "+str(self.coordinator.data))

        value = self.coordinator.data.get(FANS, {}).get(self.idx.get("id"))
        if (value == 'None') or (value is None):
            self._attr_native_value = 0
        else:
            self._attr_native_value = value


        self.async_write_ha_state()