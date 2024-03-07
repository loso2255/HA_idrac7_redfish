import logging

import redfish
from redfish.rest.v1 import HttpClient

from .const import General, ManagersGeneral, SystemsGeneral

_LOGGER = logging.getLogger(__name__)


class RedfishApihub:
    def __init__(self, ip: str, user: str, password: str):
        self.ip = ip
        self.user = user
        self.password = password

        self.logget = None
        # self.logget = self.singleton_login()

        self.MembersCount = 0
        self.lsEmmeddedSystem = []
        # self.lsEmmeddedSystem = self.getEmbeddedSystem()

        self.ManagersCount = 0
        self.lsEmmeddedManagers = []
        # self.lsEmmeddedManagers = self.getEmbeddedManagers()

    def singleton_login(self) -> HttpClient:
        if self.logget is None:
            self.logget = redfish.redfish_client(base_url="https://" + self.ip)
            self.logget.login(username=self.user, password=self.password)
            _LOGGER.info(msg="maked login")

            # assert self.logget is not None
            return self.logget

        assert self.logget is not None
        _LOGGER.info(msg="already login")
        return self.logget

    def getSysInfo(self) -> dict[str, str]:
        dictionary = {}

        dictionary["ServiceTag"] = self.getServiceTag()
        dictionary["Members"] = self.getEmbeddedSystem()
        dictionary["Managers"] = self.getEmbeddedManagers()

        return dictionary

    def getServiceTag(self) -> str:
        login = self.singleton_login()
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

    # deletion of class
    def __del__(self):
        if self.logget is not None:
            self.logget.logout()
