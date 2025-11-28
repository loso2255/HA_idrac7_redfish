"""Constants for the HA_idrac7_redfish integration."""

from string import Template

DOMAIN = "HA_idrac7_redfish"

#ciao

### V1
# config entry.data example
# {"authdata":
#           {CONF_HOST: "0.0.0.0", CONF_USERNAME: "myname", CONF_PASSWORD: "supersecret"},
#  "info":
#           {"ServiceTag": "xxxxx",  'Members':
#                                             [{'enable': False, 'id': 'System.Embedded.x'}],
#                                   'Managers':
#                                             [{'enable': False, 'id': 'iDRAC.Embedded.x'}] }
#           }


#### idea V2
# config entry.data example
# questo e un esempio di cosa dovrebbe resistituire la funzione get_systems_info(DOMAIN: str)
#{"authdata":
#           {CONF_HOST: "0.0.0.0", SKIP_SSL=True, CONF_USERNAME: "myname", CONF_PASSWORD: "supersecret"},
#  "info":
#           { "SystemId": "xxxxx",  'Members':
#                                             [{'sub-id': '1',      'DeviceInfo' : {
#                                                                                           'identifier' : { ('DOMAIN', SystemId: str + sub-id : str ) }
#                                                                                           'name' : <HostName> : str
#                                                                                           'manufacturer' : str
#                                                                                           'model' : str
#                                                                                           'sw_version' : <biosVersion> : str
#                                                                                           'managed_by' : str
#
#
#                                                                                   },
#                                                                   'DeviceSensor' : {
#                                                                                                'SystemBooleanSensorInfo' : {
#                                                                                                       'SystemInfoState' : listSystemInfoStateID[] = ['PowerState', 'HealthState', ...]
#                                                                                                       'cpuTemp' : listcpuID[] = [{id: 'CPU1Temp', unit: 'Celsius'}, '{id: 'CPU2Temp', unit: 'Celsius'}', ...]
#                                                                                                       'fans' : listfansID[] = ['Fan1', 'Fan2', ...]
#                                                                                                       'TemperatureSensor' listfansID[], ['nameSensor1', ]
#                                                                                                       'PSU' : listPSUID[]
#
#                                                                                                      },
#                                                                                               'SystemNumericSensorInfo' : {
#                                                                                                       'cpuTemp' : listcpuID[] = ['CPU1Temp', 'CPU2Temp', ...]
#                                                                                                       'fans' : listfansID[] = ['Fan1', 'Fan2', ...]
#                                                                                                       'TemperatureSensor' : [{'id' : <nameSensor>: str}, ]
#                                                                                                       'PSU' : listPSUID[]
#
#                                                                                                      },
#                                                                                               'SystemActions' : {
#                                                                                                       'PowerAction' : listPowerActionID[]
#                                                                                                       'nextFirstBoot' : listPowerActionID[]
#                                                                                                       }
#                                               }],
#                                   'Managers':
#                                             [{'sub-id': '1', 'DeviceInfo' : {
#                                                                                                       'identifier' : { ('DOMAIN', SystemId: str + sub-id : str ) }
#                                                                                                       'name' : <HostName> : str
#                                                                                                       'manufacturer' : str
#                                                                                                       'model' : str
#                                                                                                       'sw_version' : <biosVersion> : str
#
#
#                                                                                                       },
#                                                                                                'SystemBooleanSensorInfo' : {
#                                                                                                       'SystemInfoState' : listSystemInfoStateID[] = ['PowerState', 'HealthState', ...]
#
#                                                                                                      },
#                                                                                               'SystemNumericSensorInfo' : {},
#                                                                                               'SystemActions' : {
#                                                                                                       'PowerAction' : listPowerActionID[]
#
#                                                                                                       }
#
#
#                                                                            }]
#           }




##################################
#
#   static utility
#
##################################

manufacturer = "manufacturer"
model = "model"


DELAY_TIME = 'time_delay'

#Delay polling time
SERVER_POWER_STATUS_POOL = 5

##################################
#
#   API Request Management
#
##################################

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Seconds between retries: 2, 4, 8
RETRY_STATUSES = [429, 500, 502, 503, 504]  # HTTP statuses to retry

# Rate limiting
MIN_TIME_BETWEEN_REQUESTS = 0.5  # Minimum seconds between API calls
MAX_CONCURRENT_REQUESTS = 2  # Maximum parallel requests to iDRAC

# Coordinator update intervals (in seconds)
UPDATE_INTERVAL_FAST = 30  # For critical data (power status, health)
UPDATE_INTERVAL_NORMAL = 60  # For sensor data (temperature, fans)
UPDATE_INTERVAL_SLOW = 300  # For static data (system info)

# Priority levels for request queue
PRIORITY_CRITICAL = 0  # Power actions, critical commands
PRIORITY_HIGH = 1      # Status updates (power, health)
PRIORITY_NORMAL = 2    # Sensor readings
PRIORITY_LOW = 3       # Static info updates


#TIMEOUT API request
REQUEST_FOR_STATUS_POWER = 10  # Increased from 5
REQUEST_FOR_STATUS_HEALTH = 10  # Increased from 5
REQUEST_SENSOR = 15  # Increased from 8
REQUEST_TIMEOUT_DEFAULT = 20  # Default timeout for other requests

#type of sensor
FANS = "Fan"
WATTSENSOR = "Watt"
TEMPERATURE = "Temp"
PSU = "PSU"

#map sensor to api value
TotalWattConsumption = "PowerConsumedWatts"

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
ChassisConsumptions = Template('/redfish/v1/Chassis/$EmbeddedSystemID/Power/PowerControl')
#Sensor powerPSU
ChassisPSU = Template('/redfish/v1/Chassis/$EmbeddedSystemID/Power/PowerSupplies/$PSUid')

#thermal Senor
ChassisGenThermal = Template("/redfish/v1/Chassis/$EmbeddedSystemID/Thermal")
ChassisThermal = Template('/redfish/v1/Chassis/$EmbeddedSystemID/Sensors/Temperatures/$ThermalSensorID')


#Managers
ManagersGeneral = "/redfish/v1/Managers"

#SetPowerStatus
SetPowerStatus = Template("/redfish/v1/Systems/$EmbeddedSystemID/Actions/ComputerSystem.Reset")



AccountService = Template("/redfish/v1/Managers/$EmbeddedSystemID/AccountService")