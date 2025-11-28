import logging
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.const import UnitOfElectricPotential
from homeassistant.core import callback

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator


#local import

from ...const import PSU

_LOGGER = logging.getLogger(__name__)


class PSUSensor(CoordinatorEntity, SensorEntity):
    """The iDrac's current PSU voltage sensor entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, idx : str, device_info: DeviceInfo, infoSingleSystem : dict) ->None:

        super().__init__(coordinator, context=idx)

        self.idx = eval(idx)

        getNPSU = self.idx.get("id").split(".")
        getNPSU = getNPSU[len(getNPSU)-1]


        self.entity_description = SensorEntityDescription(
            key='PSU Voltage '+getNPSU,
            name='PSU Voltage '+getNPSU,
            icon='mdi:power-plug',
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT
        )

        self.id_psu = idx

        self._attr_device_info = device_info
        self._attr_unique_id = infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id']+"_"+idx
        self._attr_has_entity_name = True

        # PSU attributes
        self._voltage = None
        self._psu_name = None
        self._power_output_watts = None
        self._power_capacity_watts = None
        self._health_status = None
        self._model = None
        self._serial_number = None

        #coordinator._schedule_refresh()


    @property
    def name(self):
        """Name of the entity."""
        return self.entity_description.name

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._voltage is not None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = {}

        if self._psu_name is not None:
            attributes["psu_name"] = self._psu_name
        if self._power_output_watts is not None:
            attributes["power_output_watts"] = self._power_output_watts
        if self._power_capacity_watts is not None:
            attributes["power_capacity_watts"] = self._power_capacity_watts
        if self._health_status is not None:
            attributes["health_status"] = self._health_status
        if self._model is not None:
            attributes["model"] = self._model
        if self._serial_number is not None:
            attributes["serial_number"] = self._serial_number

        return attributes

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        #_LOGGER.info("update the info of the PSU: "+self.idx.get("id"))
        #_LOGGER.info("coordinator data PSU Status: "+str(self.coordinator.data))

        psu_data = self.coordinator.data.get(PSU, {}).get(self.idx.get("id"))

        if psu_data is None or not isinstance(psu_data, dict):
            self._voltage = None
            self._psu_name = None
            self._power_output_watts = None
            self._power_capacity_watts = None
            self._health_status = None
            self._model = None
            self._serial_number = None
        else:
            # Extract voltage (primary state)
            voltage = psu_data.get('LineInputVoltage')
            if voltage is None or voltage == 'None':
                self._voltage = None
            else:
                try:
                    self._voltage = float(voltage)
                except (ValueError, TypeError):
                    self._voltage = None

            # Extract additional attributes
            self._psu_name = psu_data.get('Name')
            self._power_output_watts = psu_data.get('LastPowerOutputWatts')
            self._power_capacity_watts = psu_data.get('PowerCapacityWatts')
            self._health_status = psu_data.get('Health')
            self._model = psu_data.get('Model')
            self._serial_number = psu_data.get('SerialNumber')

        self._attr_native_value = self._voltage
        self.async_write_ha_state()
