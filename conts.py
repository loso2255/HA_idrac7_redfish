"""Constants for the HA_idrac7_redfish integration."""

DOMAIN = "HA_idrac7_redfish"


####################################################################
#
#   API IDRAC CALL
#
##################################

General = "/redfish/v1/"

SystemsGeneral = "/redfish/v1/Systems"
SystemSpecific = "/redfish/v1/Systems/$EmbeddedSystemID"
SystemSetPowerStatus = (
    "/redfish/v1/Systems/$EmbeddedSystemID/Actions/ComputerSystem.Reset"
)

ManagersGeneral = "/redfish/v1/Managers"


AccountService = "/redfish/v1/Managers/$EmbeddedSystemID/AccountService"


Chassis = "/redfish/v1/Chassis"
ChassisReset = "/redfish/v1/Chassis/$EmbeddedSystemID/Actions/Chassis.Reset"
