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
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow, OptionsFlowWithConfigEntry
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_DELAY
from homeassistant.core import HomeAssistant, callback

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
                _LOGGER.exception("name server: [%s] Retries Exhausted: maybe the server is unreachable", user_input[CONF_HOST])
                errors["base"] = "Retries Exhausted: maybe the server is unreachable"

            except ServerDownOrUnreachableError:
                _LOGGER.exception("name server: [%s] server unreachable", user_input[CONF_HOST])
                errors["base"] = "server unreachable"

            except SessionCreationError:
                _LOGGER.exception("name server: [%s] can't connect to server", user_input[CONF_HOST])
                errors["base"] = "cannot_connect"

            except InvalidCredentialsError:
                _LOGGER.exception("name server: [%s] invalid_auth", user_input[CONF_HOST])
                errors["base"] = "invalid_auth"

            except Exception as exp:
                _LOGGER.exception("name server: [] %s", str(exp))
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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


###############################
#
#       OptionsFlowHandler
#
###############################
class OptionsFlowHandler(OptionsFlowWithConfigEntry):
    """Handle options flow for iDRAC Redfish integration."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        super().__init__(config_entry)
        self.embedded_systems = config_entry.data["info"]["Members"]
        self.config_data = dict(config_entry.data)
        self.auth_data = dict(config_entry.data["authdata"])

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            # Update polling time if provided
            if DELAY_TIME in user_input:
                self.auth_data[DELAY_TIME] = user_input[DELAY_TIME]

            # Update enabled status for each embedded system
            updated_systems = []
            for system in self.embedded_systems:
                system_id = system["id"]
                updated_system = dict(system)
                if system_id in user_input:
                    updated_system["enable"] = user_input[system_id]
                updated_systems.append(updated_system)

            # Create updated data structure
            updated_data = dict(self.config_data)
            updated_data["authdata"] = self.auth_data
            updated_data["info"] = dict(self.config_data["info"])
            updated_data["info"]["Members"] = updated_systems

            # Update managers status
            updated_managers = self._update_manager_status(
                updated_systems,
                self.config_data["info"]["Managers"]
            )
            updated_data["info"]["Managers"] = updated_managers

            # Update config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=updated_data,
            )

            # Trigger entity reload to apply changes
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        # Create schema for options flow
        options_schema = {
            vol.Required(
                DELAY_TIME,
                default=self.auth_data.get(DELAY_TIME, "30")
            ): vol.All(str, vol.Coerce(str))
        }

        # Add embedded system selection options
        for system in self.embedded_systems:
            system_id = system["id"]
            system_name = system.get("name", system_id)
            options_schema[vol.Required(
                system_id,
                default=system.get("enable", True)
            )] = bool

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options_schema),
            description_placeholders={
                "service_tag": self.config_data["info"]["ServiceTag"],
                "host": self.config_data["authdata"][CONF_HOST],
            }
        )

    def _update_manager_status(
        self, embedded_systems: list[dict[str, Any]], managers: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Update manager status based on enabled embedded systems."""
        # Create a copy of managers to update
        updated_managers = [dict(manager) for manager in managers]

        # Create a mapping from system to manager ID
        system_manager_map = {}

        # For each embedded system, determine its manager
        for system in embedded_systems:
            system_id = system["id"]

            # Extract manager ID based on naming convention
            manager_id = None

            # From system ID like "System.Embedded.1" to manager ID "iDRAC.Embedded.1"
            if "." in system_id:
                parts = system_id.split(".")
                if len(parts) >= 3:
                    manager_id = f"iDRAC.{parts[1]}.{parts[2]}"

            # Fallback to name-based correlation
            if not manager_id:
                for manager in updated_managers:
                    if system_id.replace("System", "iDRAC") == manager["id"]:
                        manager_id = manager["id"]
                        break

            if manager_id:
                system_manager_map[system_id] = manager_id

        # First, disable all managers
        for manager in updated_managers:
            manager["enable"] = False

        # Enable managers that have at least one enabled system
        for system in embedded_systems:
            if system.get("enable", False):
                manager_id = system_manager_map.get(system["id"])
                if manager_id:
                    for manager in updated_managers:
                        if manager["id"] == manager_id:
                            manager["enable"] = True
                            break

        return updated_managers


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