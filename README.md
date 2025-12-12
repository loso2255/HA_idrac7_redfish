# HA_idrac7_redfish

installation with home assistant vscode server:

right click -> create a folder named -> custom_components

or

mkdir custom_components

cd custom_components

git clone https://github.com/loso2255/HA_idrac7_redfish.git

-----------------------------------------------------

## IMPORTANT NOTE
- in order to get a correct info retrival from idrac redfish, the initial configuration MUST be done with the server powered ON (power ON the server before try to add the device to home assistant).
  this i because redfish does not expose all' sensor when the server is in off state

- this plugin should work with any idrac Version but is only teste on my Idrac7

- please report any bug in the issue

--------------------------------
# structural idea / Roadmap

- with 1 redfish session (singleton login) [OK]

- handle each sub_device like Embedded.System.1 or Embedded.System.2 or iDrac.Managers.1 ecc...
  separately [OK]

-  add sensor:
    -  power status [OK]
    -  general Health Status [OK]
    -  Fan RPM speed [OK]
    -  Power Usage [OK]
    -  PSU input voltage [OK]
    -  Temperature from idrac [OK]

-  add button:
    -  button for change power status of the server [OK]

- each sub_device can be registered or not in the config_flow (and later added or removed)  [OK]
- add the possibility to modify credential, and enable or disable system [OK]
