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
from homeassistant.helpers.selector import BooleanSelector

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
class RedfishIdracConfigFlow(ConfigFlow, domain=DOMAIN):
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
            self.update_manager_status()

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

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle initial options selection."""

        return self.async_show_menu(step_id="init", menu_options=["credentials", "systems"], )

    async def async_step_credentials(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle credentials update."""

        errors: dict[str, str] = {}

        if user_input is not None:
            # Test new credentials
            try:
                await validate_input(self.hass, user_input)
            except RetriesExhaustedError:
                errors["base"] = "retries_exhausted"
            except ServerDownOrUnreachableError:
                errors["base"] = "cannot_connect"
            except SessionCreationError:
                errors["base"] = "cannot_connect"
            except InvalidCredentialsError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Update config entry with new credentials
                new_data = {**self.config_entry.data}

                # Update auth data in the nested structure
                if "authdata" in new_data:
                    new_data["authdata"].update(user_input)
                else:
                    # Flat structure - update directly
                    new_data.update(user_input)

                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )

                # Trigger reload of the integration
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)

                return self.async_create_entry(title="", data={})

        # Get current credentials
        auth_data = self.config_entry.data.get("authdata", self.config_entry.data)

        credentials_schema = vol.Schema({
            vol.Required(
                CONF_HOST,
                default=auth_data.get(CONF_HOST)
            ): str,
            vol.Required(
                CONF_USERNAME,
                default=auth_data.get(CONF_USERNAME)
            ): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(
                DELAY_TIME,
                default=auth_data.get(DELAY_TIME, "30")
            ): str,
        })

        return self.async_show_form(
            step_id="credentials",
            data_schema=credentials_schema,
            errors=errors,
            description_placeholders={
                "service_tag": self.config_entry.data.get("info", {}).get("ServiceTag", "Unknown"),
                "host": auth_data.get(CONF_HOST),
            },
        )

    async def async_step_systems(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle systems and managers configuration."""
        if user_input is not None:
            # Get current data structure
            new_data = dict(self.config_entry.data)

            # Update embedded systems configuration
            if "info" in new_data and "Members" in new_data["info"]:
                updated_systems = []
                for system in new_data["info"]["Members"]:
                    updated_system = dict(system)
                    if system_id := updated_system.get("id"):
                        if system_id in user_input:
                            updated_system["enable"] = user_input[system_id]
                    updated_systems.append(updated_system)

                # Update managers status based on new system configuration
                updated_managers = update_manager_status(updated_systems, new_data["info"].get("Managers", []) )

                # Update the data structure
                new_data["info"]["Members"] = updated_systems
                new_data["info"]["Managers"] = updated_managers

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )

            # Trigger reload of the integration
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        # Create systems selection schema with better labels
        options_schema = {}
        embedded_systems = self.config_entry.data.get("info", {}).get("Members", [])

        for system in embedded_systems:
            system_id = system["id"]
            # Get current enable status - default to True if not specified
            current_status = system.get("enable", True)

            options_schema[
                vol.Required(system_id, default=current_status, description={"suggested_value": current_status})
            ] = bool

        return self.async_show_form(
            step_id="systems",
            data_schema=vol.Schema(options_schema),
            description_placeholders={
                "service_tag": self.config_entry.data.get("info", {}).get("ServiceTag", "Unknown"),
                "host": self.config_entry.data.get("authdata", {}).get(CONF_HOST, "Unknown"),
            },
        )


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


def update_manager_status(embedded_systems: list[dict[str, Any]], managers: list[dict[str, Any]]) -> list[dict[str, Any]]:

    """Update manager status based on embedded systems."""
    updated_managers = [dict(m) for m in managers]
    system_manager_map: dict[str, str] = {}

    for system in embedded_systems:
        system_id = system["id"]
        manager_id = None

        if "." in system_id:
            parts = system_id.split(".")
            if len(parts) >= 3:
                manager_id = f"iDRAC.{parts[1]}.{parts[2]}"

        if not manager_id:
            for manager in updated_managers:
                if system_id.replace("System", "iDRAC") == manager["id"]:
                    manager_id = manager["id"]
                    break

        if manager_id:
            system_manager_map[system_id] = manager_id

    # Disable all managers first
    for manager in updated_managers:
        manager["enable"] = False

    # Enable managers that have at least one enabled system
    for system in embedded_systems:
        if system.get("enable"):
            if manager_id := system_manager_map.get(system["id"]):
                for manager in updated_managers:
                    if manager["id"] == manager_id:
                        manager["enable"] = True
                        break

    return updated_managers