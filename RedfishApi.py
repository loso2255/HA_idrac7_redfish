import logging

import redfish
from redfish.rest.v1 import HttpClient

from .const import ChassisFans, General, ManagersGeneral, SetPowerStatus, SystemSpecific, SystemsGeneral

_LOGGER = logging.getLogger(__name__)


class RedfishApihub:
    def __init__(self, ip: str, user: str, password: str):
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

        #first login
        if self.logget is None:
            self.logget = redfish.redfish_client(base_url="https://" + self.ip, max_retry=1)

            self.logget.login(username=self.user, password=self.password)

            _LOGGER.info(msg="maked login")

            # assert self.logget is not None
            return self.logget

        #if already logged
        elif self.logget is not None:

            #test sessions
            _LOGGER.info(msg="test session")
            res = self.logget.get(ManagersGeneral)

            if res.status == 401:
                _LOGGER.info("Re oauth in progress")
                self.logget.login(username=self.user, password=self.password)

            else:
                _LOGGER.info(msg="session ok")

            return self.logget



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
        lsEmmeddedManagers = resp.dict["Members"]

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
        logged = self.singleton_login()

        dictionary = {}

        resRedfish = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idEmbSys)}))
        #_LOGGER.info(msg=str(resRedfish))

        dictionary["name"] = resRedfish.dict['HostName']
        dictionary["model"] = resRedfish.dict['Model']
        dictionary["manufacturer"] = resRedfish.dict['Manufacturer']
        dictionary["sw_version"] = resRedfish.dict['BiosVersion']

        return dictionary

    def getEmbSysPowerActions(self, idEmbSys) -> list[str]:
        logged = self.singleton_login()

        resRedfish = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idEmbSys)}))
        #_LOGGER.info(msg=str(resRedfish))

        return resRedfish.dict['Actions']['#ComputerSystem.Reset']['ResetType@Redfish.AllowableValues']


    def getEmbeddedSystemCooledBy(self, idEmbSys) -> list[str]:
    # {
        logged = self.singleton_login()

        resp = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idEmbSys)}))
        lsFan = resp.dict["Links"]["CooledBy"]
        _LOGGER.info( "all fans cooling raw: " + str(lsFan) )

        fanID = []

        for elm in lsFan:
            id_elm = elm["@odata.id"].split("/")
            fanID.append( id_elm[(len(id_elm) - 1)] )

        return fanID
    # }



    #
    # poolling functions

    def getpowerState(self, idEmbSys) -> dict[str, str]:
        logged = self.singleton_login()

        dictionary = {}

        resRedfish = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idEmbSys)}))
        dictionary["state"] = resRedfish.dict['PowerState']

        return dictionary


    def getHealthStatus(self, idEmbSys) -> dict[str, str]:
        logged = self.singleton_login()

        dictionary = {}

        resRedfish = logged.get(SystemSpecific.substitute({'EmbeddedSystemID' : str(idEmbSys)}))
        dictionary["health"] = resRedfish.dict['Status']['Health']

        return dictionary

    def pressPowerStatusButton(self, idEmbSys , actions : str):
        logged = self.singleton_login()

        resRedfish = logged.post(path=SetPowerStatus.substitute({'EmbeddedSystemID' : str(idEmbSys)}), body={ 'ResetType': actions } )
        #_LOGGER.info("res status power button: "+str(resRedfish.status))
        #_LOGGER.info("res power button: "+str(resRedfish))


    def getFanSensor(self, idEmbSys, idFan):
    # {
        logged = self.singleton_login()

        resp = logged.get( path = ChassisFans.substitute( {'EmbeddedSystemID' : str(idEmbSys), 'FanID': str(idFan) } ) )

        return str(resp.dict["Reading"])
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

        dictionary["name"] = resRedfish.dict['name']
        #dictionary["model"] = resRedfish.dict['Model']
        #dictionary["manufacturer"] = resRedfish.dict['Manufacturer']
        dictionary["sw_version"] = resRedfish.dict['FirmwareVersion']

        return dictionary





    # deletion of class
    def __del__(self):
        if self.logget is not None:
            self.logget.logout()
