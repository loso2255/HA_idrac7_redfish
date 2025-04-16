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

# data form
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(DELAY_TIME, default="30"): str,
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
        self.EmbeddedSystem_list: list[dict[str, Any]] = []
        self.iDrac_list: list[dict[str, Any]] = []
        self.service_tag: str = ""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            info: dict[str, Any] = {}
            try:
                info = await validate_input(self.hass, user_input)

            except RetriesExhaustedError:
                _LOGGER.exception("Name server: [%s] Retries Exhausted: maybe the server is unreachable", user_input[CONF_HOST])
                errors["base"] = "Retries Exhausted: maybe the server is unreachable"

            except ServerDownOrUnreachableError:
                _LOGGER.exception("Name server: [%s] server unreachable", user_input[CONF_HOST])
                errors["base"] = "server unreachable"

            except SessionCreationError:
                _LOGGER.exception("Name server: [%s] can't connect to server", user_input[CONF_HOST])
                errors["base"] = "cannot_connect"

            except InvalidCredentialsError:
                _LOGGER.exception("Name server: [%s] invalid_auth", user_input[CONF_HOST])
                errors["base"] = "invalid_auth"

            except Exception as exp:
                _LOGGER.exception("Name server: [] %s", str(exp))
                errors["base"] = "unknown exception"
                return self.async_abort(reason="unknown exception check logs")

            else:
                assert info is not None

                # If already configured
                if await self.api_alias_already_configured(info):
                    return self.async_abort(reason="already_configured")

                # Save data for next step
                self.Redfish_config = user_input
                self.EmbeddedSystem_list = info["info"].get("Members", [])
                self.iDrac_list = info["info"].get("Managers", [])
                self.service_tag = info["info"].get("ServiceTag", "")

                # Proceed to embedded systems configuration
                return await self.async_step_embsys()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_embsys(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the embedded systems selection step."""

        if user_input is not None:
            # Apply user selections to embedded systems
            for system in self.EmbeddedSystem_list:
                system_id = system["id"]
                if system_id in user_input:
                    system["enable"] = user_input[system_id]

            # Update manager status based on enabled systems
            self._update_manager_status()

            # Create config entry with complete data
            config_data = {
                "authdata": self.Redfish_config,
                "info": {
                    "ServiceTag": self.service_tag,
                    "Members": self.EmbeddedSystem_list,
                    "Managers": self.iDrac_list
                }
            }

            # Include the iDRAC host IP in the entry title
            entry_title = f"{self.service_tag} ({self.Redfish_config[CONF_HOST]})"

            return self.async_create_entry(
                title=entry_title,
                data=config_data,
            )

        # Create schema for embedded systems selection
        schema = {}
        for system in self.EmbeddedSystem_list:
            schema[vol.Required(system["id"], default=system.get("enable", True))] = bool

        return self.async_show_form(
            step_id="embsys",
            data_schema=vol.Schema(schema),
            description_placeholders={"service_tag": self.service_tag}
        )

    def _update_manager_status(self) -> None:
        """Update manager status based on enabled embedded systems."""
        # Create a mapping from system to manager ID
        system_manager_map = {}

        # For each embedded system, determine its manager based on the path pattern
        for system in self.EmbeddedSystem_list:
            system_id = system["id"]
            system_path = system.get("path", "")

            # Extract manager ID from the path or correlate based on naming convention
            # This is a simplification - adjust based on actual path structure
            manager_id = None

            # Example: from system path '/redfish/v1/Systems/System.Embedded.1'
            # to manager ID 'iDRAC.Embedded.1'
            if "." in system_id:
                parts = system_id.split(".")
                if len(parts) >= 3:
                    manager_id = f"iDRAC.{parts[1]}.{parts[2]}"

            # Fallback: try to find a manager with a similar ID pattern
            if not manager_id:
                # Try to derive manager ID using other logic
                for manager in self.iDrac_list:
                    if system_id.replace("System", "iDRAC") == manager["id"]:
                        manager_id = manager["id"]
                        break

            if manager_id:
                system_manager_map[system_id] = manager_id

        # First, disable all managers
        for manager in self.iDrac_list:
            manager["enable"] = False

        # Then enable managers that have at least one enabled system
        for system in self.EmbeddedSystem_list:
            if system.get("enable", False):
                manager_id = system_manager_map.get(system["id"])
                if manager_id:
                    for manager in self.iDrac_list:
                        if manager["id"] == manager_id:
                            manager["enable"] = True
                            break

    # Check if entry already exists
    async def api_alias_already_configured(self, user_input: dict[str, Any]) -> bool:
        """Check if the system is already configured."""
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
    hub = RedfishApihub(data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD])
    info = await hass.async_add_executor_job(hub.getRedfishInfo)

    system_info = {}
    system_info["authdata"] = data
    system_info["info"] = info

    await hass.async_add_executor_job(hub.__del__)
    return system_info