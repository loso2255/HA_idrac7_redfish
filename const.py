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

DELAY_TIME = 'time_delay'
SERVER_POWER_STATUS_POOL = 5

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

#sensor Fans
ChassisFans = Template('/redfish/v1/Chassis/$EmbeddedSystemID/Sensors/Fans/$FanID')

#PowerConsumptions
ChassisConsumptions = Template('/redfish/v1/Chassis/$EmbeddedSystemID/Power')
#Sensor powerPSU
ChassisPSU = Template('/redfish/v1/Chassis/$EmbeddedSystemID/Power/PowerSupplies/$PSUid')



#Managers
ManagersGeneral = "/redfish/v1/Managers"

#SetPowerStatus
SetPowerStatus = Template("/redfish/v1/Systems/$EmbeddedSystemID/Actions/ComputerSystem.Reset")



AccountService = Template("/redfish/v1/Managers/$EmbeddedSystemID/AccountService")