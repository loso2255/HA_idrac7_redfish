"""Constants for the HA_idrac7_redfish integration."""

from string import Template

DOMAIN = "HA_idrac7_redfish"



###
# config entry.data example
# {"authdata":
#           {CONF_HOST: "0.0.0.0", CONF_USERNAME: "myname", CONF_PASSWORD: "supersecret"},
#  "info":
#           {"ServiceTag": "xxxxx",  'Members':
#                                             [{'enable': False, 'id': 'System.Embedded.x'}],
#                                   'Managers':
#                                             [{'enable': False, 'id': 'iDRAC.Embedded.x'}] }
#           }


##################################
#
#   static utility
#
##################################

manufacturer = "manufacturer"
model = "model"



####################################################################
#
#   API IDRAC CALL
#
##################################

General = "/redfish/v1/"


#software info
SystemsGeneral = "/redfish/v1/Systems"
SystemSpecific = Template("/redfish/v1/Systems/$EmbeddedSystemID")
SystemSetPowerStatus = Template("/redfish/v1/Systems/$EmbeddedSystemID/Actions/ComputerSystem.Reset")

#sensor info
Chassis = "/redfish/v1/Chassis"
ChassisSpecific = Template("/redfish/v1/Chassis/$EmbeddedSystemID")
ChassisReset = Template("/redfish/v1/Chassis/$EmbeddedSystemID/Actions/Chassis.Reset")

#Managers
ManagersGeneral = "/redfish/v1/Managers"


AccountService = Template("/redfish/v1/Managers/$EmbeddedSystemID/AccountService")





