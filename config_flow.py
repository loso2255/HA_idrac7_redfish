"""Config flow for HA_idrac7_redfish integration."""
from __future__ import annotations

import logging
from typing import Any

from redfish.rest.v1 import (
    InvalidCredentialsError,
    RetriesExhaustedError,
    ServerDownOrUnreachableError,
    SessionCreationError,
)


import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_DELAY
from homeassistant.core import HomeAssistant

from .RedfishApi import RedfishApihub
from .const import DELAY_TIME, DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need

# data form
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(DELAY_TIME): str,
    }
)




###############################
#
#       ConfigFlow
#
###############################
class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA_idrac7_redfish."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        self._entry = None

        self.Redfish_config: dict[str, Any] = {}
        self.EmbeddedSystem_list: dict[str, Any] = {}
        self.iDrac_list: dict[str, Any] = {}

    # ConfigFlowResult non yet implemented use FlowResult
    async def async_step_user( self, user_input: dict[str, Any] | None = None ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            info: dict[str, Any] = {}
            try:
                info = await validate_input(self.hass, user_input)

            except RetriesExhaustedError:
                _LOGGER.exception(msg="name server: ["+ user_input[CONF_HOST]+ "] Retries Exhausted: maybe the server is unreachable")

                errors["base"] = "Retries Exhausted: maybe the server is unreachable"

            except ServerDownOrUnreachableError:
                _LOGGER.exception(msg="name server: ["+ user_input[CONF_HOST]+ "] server unreachable")

                errors["base"] = "server unreachable"

            except SessionCreationError:
                _LOGGER.exception(msg="name server: ["+ user_input[CONF_HOST]+ "] can't connect to server")

                errors["base"] = "cannot_connect"

            except InvalidCredentialsError:
                _LOGGER.exception(msg="name server: [" + user_input[CONF_HOST] + "] invalid_auth")
                errors["base"] = "invalid_auth"

            except Exception as exp:
                _LOGGER.exception(msg="name server: [" + "" + "]" + str(exp))
                
                errors["base"] = "unknown exception"
                return self.async_abort(reason="unknown exception check logs")

            else:
                assert info is not None
                #_LOGGER.info(msg="dentro config_flow.setup_user: " + str(info))


                #if already configured
                if await self.api_alias_already_configured(info):
                    return self.async_abort(reason="already_configured")


                return self.async_create_entry(
                    title=info["info"]["ServiceTag"], data=info,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    # for the future (enable disable registration of device)
#    async def async_step_EmbSys(self, user_input: dict[str, Any] | None = None ) -> ConfigFlowResult:
#
#            #show list of embedded system

#                embedded_Sys_schema : dict = {}
#                for elm in info["info"]["Members"]:
#                    embedded_Sys_schema[vol.Required(elm['id'], default=elm['enable'])] = bool

#                return self.async_show_form(step_id="embeddedSys", data_schema=vol.Schema({ vol.Required("ciao", default=False) : bool}))




    #check if entry already exist
    async def api_alias_already_configured(self, user_input: dict[str, Any]) -> bool:

        for entry in self._async_current_entries():

            if entry.data["info"]["ServiceTag"] == user_input["info"]["ServiceTag"]:
                return True

        return False



##########################
#
#   utility functions
#
##########################

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data[CONF_USERNAME], data[CONF_PASSWORD]
    # )


    hub = RedfishApihub(data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD])
    info = await hass.async_add_executor_job(hub.getRedfishInfo)

    #get DeviceInfo

    #get ChassisInfo

    system_info = {}
    system_info["authdata"] = data
    system_info["info"] = info

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth
    #_LOGGER.info(msg="dentro dentro config_flow.validate_input: " + str(info))

    await hass.async_add_executor_job(hub.__del__)
    # Return info that you want to store in the config entry.
    return system_info