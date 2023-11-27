# cBioPortal-BeaconV2

Script to map cBioPortal data to Beacon v2.

Before running the script check [basicConfigFile.ini](basicConfigFile.ini). You must put your Study ID in the field `studyId`. Then, change your clinical data fields to match the ones in your study. If not, the script will map to the base fields given by cBioPortal.

To map the Individual and Biosample schema it is recommended to use the Beacon v2 schema from the [main repository](https://github.com/SergiAguilo/cBioPortal-BeaconV2). 

- Usage

```
python3 cBioPortalBeaconMapping.py basicConfigFile.ini
```

This script create Beacon Friendly Format (BFF) files compatible to the Reference Implementation BeaconV2 API.

## Light a Beacon (beta version)

For creating a BeaconV2 working instance, you can use the (Reference Implementation)[https://github.com/EGA-archive/beacon2-ri-api] developed at the Centre for Genomic Regulation (CRG). 

# License

* GNU AFFERO GENERAL PUBLIC LICENSE Version 3. Ver [`LICENSE.md`](LICENSE.md).
* [![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-brightgreen)](https://www.gnu.org/licenses/gpl-3.0.en.html) 

# Acknowlegment

This repo is a discarded work from in the [IMPaCT-Data](https://impact-data.bsc.es/) project, with the support of Instituto de Salud Carlos III and the Barcelona SuperComputing Center.

The original on-the-fly work can be found in the [IMPaCT-Data repo](https://gitlab.bsc.es/impact-data/impd-beacon_cbioportal).

