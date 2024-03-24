# HA_idrac7_redfish

installation with home assistant vscode server:

right click -> create a folder named -> custom_components

or

mkdir custom_components

cd custom_components

git clone https://github.com/loso2255/HA_idrac7_redfish

-----------------------------------------------------

## IMPORTANT NOTE
- this app is in early stage of development
- in order to get a correct info retrival from idrac redfish, the initial configuration must be done with the server powered ON (power ON the server before try to add the device to home assistant) 


--------------------------------
# structural idea / Roadmap

- with 1 redfish session (singleton login) [OK]

- handle each sub_device like Embedded.System.1 or Embedded.System.2 or iDrac.Managers.1 ecc...
  separately [OK]

-  add sensor:
    -  power status [OK]
    -  general Health Status [OK]
    -  Fan RPM speed [OK]
    -  Power Status [future]
    -  PSU input voltage [future]

-  add button:
    -  button for change power status of the server [OK]
  
- each sub_device can be registered or not in the config_flow (and later added or removed)  [for the future]
