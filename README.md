# HA_idrac7_redfish

installation with home assistant vscode server
right click -> create a folder named -> custom_components

cd custom_components

git clone https://github.com/loso2255/HA_idrac7_redfish

-----------------------------------------------------

## IMPORTANT NOTE
this app is in early stage of development


--------------------------------
# structural idea / Roadmap

- with 1 redfish session (singleton login)

- handle each sub_device like Embedded.System.1 or Embedded.System.2 or iDrac.Managers.1 ecc...
  separately
  
- each sub_device can be registered or not in the config_flow (and leter added or removed)
