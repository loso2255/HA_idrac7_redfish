

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo


from ...RedfishApi import RedfishApihub

class ServerPowerButton(ButtonEntity):

    def __init__(self, hass, api: RedfishApihub, device_info : DeviceInfo, infoSingleSystem : dict ) -> None:
        super().__init__()
        self.hass = hass
        self.api = api

        self.entity_description = ButtonEntityDescription(
            key='Power Actions '+infoSingleSystem['powerActions'],
            name='Power Actions '+infoSingleSystem['powerActions'],
            icon='',
            device_class=ButtonDeviceClass.UPDATE
        )

        self._attr_device_info = device_info
        self._attr_unique_id = infoSingleSystem['ServiceTag']+"_"+infoSingleSystem['id']+"_"+infoSingleSystem['powerActions']
        self._attr_has_entity_name = True

        self.id = infoSingleSystem['id']
        self.powerActions = infoSingleSystem['powerActions']



    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(self.api.pressPowerStatusButton,self.id,self.powerActions)