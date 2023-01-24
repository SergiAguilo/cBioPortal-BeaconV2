# cBioPortal-BeaconV2

Script to map cBioPortal data to Beacon v2

Before running the script check [basicConfigFile.ini](basicConfigFile.ini). You must put your Study ID in the field `studyId`. Then, change your clinical data fields to match the ones in your study. If not, the script will map to the base fields given by cBioPortal.

- Usage

```
python3 mappingAPI.py basicConfigFile.ini
```
