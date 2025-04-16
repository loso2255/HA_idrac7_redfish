import logging

import redfish
from redfish.rest.v1 import HttpClient

from .const import ChassisConsumptions, ChassisFans, ChassisGenThermal, General, ManagersGeneral, SetPowerStatus, SystemSpecific, SystemsGeneral

_LOGGER = logging.getLogger(__name__)


class RedfishApihub:
    def __init__(self, ip: str, user: str, password: str) -> None:
        self.ip : str = ip
        self.user : str = user
        self.password : str = password

        self.logget : HttpClient = None
        # self.logget = self.singleton_login()

        self.MembersCount : int = 0
        self.lsEmmeddedSystem = []
        # self.lsEmmeddedSystem = self.getEmbeddedSystem()

        self.ManagersCount : int = 0
        self.lsEmmeddedManagers = []
        # self.lsEmmeddedManagers = self.getEmbeddedManagers()



    ###################
    #
    #   utility class
    #
    ###################
    def singleton_login(self) -> HttpClient:
        """Create or return an existing authenticated Redfish client session.

        Returns:
            HttpClient: Authenticated Redfish client

        Raises:
            ConnectionError: If connection to the iDRAC fails
            InvalidCredentialsError: If authentication fails
        """
        try:
            # First login attempt
            if self.logget is None:
                _LOGGER.debug("Creating new Redfish client session")
                self.logget = redfish.redfish_client(
                    base_url="https://" + self.ip,
                    max_retry=3,
                    timeout=10
                )

                # Attempt login with credentials
                try:
                    self.logget.login(username=self.user, password=self.password)
                    _LOGGER.debug("New Redfish client session created successfully")
                    return self.logget
                except Exception as login_err:
                    self.logget = None
                    _LOGGER.error("Failed to authenticate with iDRAC: %s", str(login_err))
                    raise

            # Session already exists, verify it's still valid
            elif self.logget is not None:
                try:
                    # Test session with a lightweight request
                    res = self.logget.get(ManagersGeneral)

                    # If we get an unauthorized error, re-authenticate
                    if res.status == 401:
                        _LOGGER.debug("Session expired, re-authenticating")
                        self.logget.login(username=self.user, password=self.password)
                        _LOGGER.debug("Re-authentication successful")

                    return self.logget

                except Exception as session_err:
                    # If session test fails, try to create a new session
                    _LOGGER.debug("Session test failed: %s, creating new session", str(session_err))
                    try:
                        # Close old session if possible
                        try:
                            self.logget.logout()
                        except Exception:
                            pass

                        # Create new session
                        self.logget = redfish.redfish_client(
                            base_url="https://" + self.ip,
                            max_retry=3,
                            timeout=10
                        )
                        self.logget.login(username=self.user, password=self.password)
                        return self.logget
                    except Exception as create_err:
                        self.logget = None
                        _LOGGER.error("Failed to create new Redfish session: %s", str(create_err))
                        raise

            return self.logget

        except Exception as err:
            # Handle any uncaught exceptions
            _LOGGER.error("Error in singleton_login: %s", str(err))
            raise




    #####################
    #
    #   get redfish info
    #
    ######################
    def getRedfishInfo(self) -> dict[str, str]:
        dictionary = {}

        dictionary["ServiceTag"] = self.getServiceTag()
        dictionary["Members"] = self.getEmbeddedSystem()
        dictionary["Managers"] = self.getEmbeddedManagers()

        return dictionary

    def getServiceTag(self) -> str:
        login = redfish.redfish_client(base_url="https://" + self.ip, max_retry=1)

        ServiceTag = login.get(General).dict["Oem"]["Dell"]["ServiceTag"]
        return str(ServiceTag)


    def getEmbeddedSystem(self):
        # {
        logged = self.singleton_login()

        resp = logged.get(SystemsGeneral)
        lsEmmeddedSystem = resp.dict["Members"]

        Memebers = []

        for elm in lsEmmeddedSystem:
            id_elm = elm["@odata.id"].split("/")
            elmDict = {}
            elmDict["enable"] = False
            elmDict["id"] = id_elm[(len(id_elm) - 1)]

            Memebers.append(elmDict)

        self.MembersCount = len(lsEmmeddedSystem)
        return Memebers

    # }

    def getEmbeddedManagers(self):
    # {
        logged = self.singleton_login()

        resp = logged.get(ManagersGeneral)
        lsEmmeddedManagers = resp.dict.get("Members")

        Managers = []

        for elm in lsEmmeddedManagers:
            id_elm = elm["@odata.id"].split("/")
            elmDict = {}
            elmDict["enable"] = False
            elmDict["id"] = id_elm[(len(id_elm) - 1)]

            Managers.append(elmDict)

        self.MembersCount = len(lsEmmeddedManagers)
        return Managers

    # }


    ########################
    #
    #   api embedded system
    #
    #########################


    #
    # setup functions

    def getEmbSysInfo(self, idEmbSys) -> dict[str, str]:
    # {
        logged = self.singleton_login()

        dictionary = {}

        resRedfish = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idEmbSys)}))
        #_LOGGER.info(msg=str(resRedfish))

        dictionary["name"] = resRedfish.dict.get('HostName')
        dictionary["model"] = resRedfish.dict.get('Model')
        dictionary["manufacturer"] = resRedfish.dict.get('Manufacturer')
        dictionary["sw_version"] = resRedfish.dict.get('BiosVersion')

        return dictionary
    # }

    def getEmbSysPowerActions(self, idEmbSys) -> list[str]:
    # {
        logged = self.singleton_login()

        resRedfish = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idEmbSys)}))
        #_LOGGER.info(msg=str(resRedfish))

        return resRedfish.dict.get('Actions').get('#ComputerSystem.Reset').get('ResetType@Redfish.AllowableValues')
    # }


    def getEmbeddedSystemCooledBy(self, idEmbSys) -> list[str]:
    # {
        logged = self.singleton_login()

        resp = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idEmbSys)}))

        lsFan = resp.dict.get("Links",{}).get("CooledBy")
        #_LOGGER.info( "all fans cooling raw: " + str(lsFan) )

        fanID = []

        for elm in lsFan:
            id_elm = elm.get("@odata.id").split("/")
            fanID.append( id_elm[(len(id_elm) - 1)] )

        return fanID
    # }


    # poolling functions

    def getpowerState(self, idEmbSys) -> dict[str, str]:
        logged = self.singleton_login()

        dictionary = {}

        resRedfish = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idEmbSys)}))
        dictionary["state"] = resRedfish.dict.get('PowerState', None)

        return dictionary


    def getHealthStatus(self, idEmbSys) -> dict[str, str]:
        logged = self.singleton_login()

        dictionary = {}

        resRedfish = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idEmbSys)}))
        dictionary["health"] = resRedfish.dict.get('Status').get('Health')

        return dictionary


    def getFanSensor(self, idEmbSys, idFan):
    # {
        logged = self.singleton_login()
        #_LOGGER.info(msg="preso sensore fans: "+idFan)

        resp = logged.get( path = ChassisFans.substitute( {'EmbeddedSystemID' : str(idEmbSys), 'FanID': str(idFan) } ) )

        return str(resp.dict.get("Reading"))
    # }

    def getAllFan(self, idEmbSys):
    # {
        logged = self.singleton_login()

        resp = logged.get( path = ChassisGenThermal.substitute( {'EmbeddedSystemID' : str(idEmbSys) } ) )

        #_LOGGER.info("response temp sensor: ", str(resp))
        vectorTemp = resp.dict.get("Fans", [])


        listAllFanSensorReading = []
        for elm in vectorTemp:

            tmp = elm.get("@odata.id")
            listAllFanSensorReading.append( logged.get( path = tmp ).dict )

        #_LOGGER.info("temp apir response: "+str(listTemperatureSensorReading))
        return listAllFanSensorReading
    # }


    def getElectricitySensor(self, idEmbSys) -> dict[str, any]:
    # {
        logged = self.singleton_login()

        resp = logged.get( path = ChassisConsumptions.substitute( {'EmbeddedSystemID' : str(idEmbSys) } ) )

        respDict : dict = {}

        respDict['PowerCapacityWatts'] = resp.dict.get('PowerCapacityWatts')
        respDict['PowerConsumedWatts'] = resp.dict.get('PowerConsumedWatts')


        Powerlimit = resp.dict.get('PowerLimit') #LimitInWatts
        if Powerlimit is not None:
            respDict['PowerLimitWatts'] = Powerlimit.get('LimitInWatts')
            respDict['PowerLimitPolicy'] = Powerlimit.get('LimitException')


        return respDict
    # }

    def getTemperatureSensor(self, idEmbSys):
    # {
        logged = self.singleton_login()

        resp = logged.get( path = ChassisGenThermal.substitute( {'EmbeddedSystemID' : str(idEmbSys) } ) )

        #_LOGGER.info("response temp sensor: ", str(resp))
        vectorTemp = resp.dict.get("Temperatures", [])


        listTemperatureSensorReading = []
        for elm in vectorTemp:

            tmp = elm.get("@odata.id")
            listTemperatureSensorReading.append( logged.get( path = tmp ).dict )

        #_LOGGER.info("temp apir response: "+str(listTemperatureSensorReading))
        return listTemperatureSensorReading

    # }

    ## azioni

    # power actions
    def pressPowerStatusButton(self, idEmbSys , actions : str):
    # {
        logged = self.singleton_login()

        resRedfish = logged.post(path=SetPowerStatus.substitute({'EmbeddedSystemID' : str(idEmbSys)}), body={ 'ResetType': actions } )
        #_LOGGER.info("res status power button: "+str(resRedfish.status))
        #_LOGGER.info("res power button: "+str(resRedfish))
    # }



    ########################
    #
    #   api manager idrac
    #
    #########################

    #
    # setup functions

    def getManiDracInfo(self, idManiDrac) -> dict[str, str]:
        logged = self.singleton_login()

        dictionary = {}

        resRedfish = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idManiDrac)}))
        #_LOGGER.info(msg=str(resRedfish))

        dictionary["name"] = resRedfish.dict.get('name')
        #dictionary["model"] = resRedfish.dict['Model']
        #dictionary["manufacturer"] = resRedfish.dict['Manufacturer']
        dictionary["sw_version"] = resRedfish.dict.get('FirmwareVersion')

        return dictionary


    ########################
    #
    #   SSE Event Support
    #
    ########################

    def check_sse_support(self) -> dict[str, bool | str]:
        """Check if the iDRAC supports Server-Sent Events.

        Returns:
            dict: Information about SSE support capabilities
                - "supports_sse": bool - True if SSE is supported
                - "event_service_supported": bool - True if Event Service endpoint exists
                - "subscription_supported": bool - True if subscriptions are supported
                - "version": str - Redfish version
                - "message": str - Descriptive message about support status
        """
        result = {
            "supports_sse": False,
            "event_service_supported": False,
            "subscription_supported": False,
            "version": "unknown",
            "message": "SSE not supported"
        }

        try:
            logged = self.singleton_login()

            # Check Redfish version
            root_data = logged.get("/redfish/v1/").dict
            result["version"] = root_data.get("RedfishVersion", "unknown")

            # Check if EventService exists
            try:
                event_service = logged.get("/redfish/v1/EventService")
                if event_service.status == 200:
                    result["event_service_supported"] = True
                    event_data = event_service.dict

                    # Check if SSE is in delivery methods
                    delivery_methods = event_data.get("DeliveryRetryPolicy", [])
                    if isinstance(delivery_methods, list) and "SSE" in delivery_methods:
                        result["supports_sse"] = True

                    # Check EventService capabilities
                    if event_data.get("ServerSentEventUri"):
                        result["supports_sse"] = True

                    # Check if subscriptions are supported
                    try:
                        subscriptions = logged.get("/redfish/v1/EventService/Subscriptions")
                        if subscriptions.status == 200:
                            result["subscription_supported"] = True
                    except Exception:
                        _LOGGER.debug("EventService subscriptions endpoint not supported")
            except Exception:
                _LOGGER.debug("EventService endpoint not supported")

            # Set appropriate message
            if result["supports_sse"]:
                result["message"] = "SSE is supported"
            elif result["event_service_supported"]:
                result["message"] = "EventService is supported, but SSE delivery may not be available"
            else:
                result["message"] = "EventService is not supported, SSE not available"

        except Exception as err:
            _LOGGER.error("Error checking SSE support: %s", err)
            result["message"] = f"Error checking SSE support: {str(err)}"

        return result

    def test_eventservice_capabilities(self) -> dict:
        """Test and return all EventService capabilities.

        Returns:
            dict: Raw EventService data if available, or error information
        """
        try:
            logged = self.singleton_login()
            event_service = logged.get("/redfish/v1/EventService")

            if event_service.status == 200:
                return event_service.dict

            return {"error": f"EventService returned status {event_service.status}"}
        except Exception as err:
            return {"error": f"Error accessing EventService: {str(err)}"}


    # deletion of class
    def __del__(self) -> None:
        """Clean up resources when this object is being garbage collected.

        Safely logs out of the Redfish session if one exists.
        """
        self._safe_logout()

    def _safe_logout(self) -> None:
        """Safely log out from the Redfish session.

        Handles exceptions and ensures proper cleanup.
        """
        if self.logget is None:
            return

        try:
            _LOGGER.debug("Logging out of Redfish session")
            self.logget.logout()
            _LOGGER.debug("Successfully logged out of Redfish session")
        except Exception as err:
            _LOGGER.debug("Error during Redfish logout: %s", str(err))
        finally:
            # Always clear the session reference
            self.logget = None
