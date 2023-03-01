# cBioPortal-BeaconV2

Script to map cBioPortal data to Beacon v2

Before running the script check [basicConfigFile.ini](basicConfigFile.ini). You must put your Study ID in the field `studyId`. Then, change your clinical data fields to match the ones in your study. If not, the script will map to the base fields given by cBioPortal.

- Usage

```
python3 cBioPortalBeaconMapping.py basicConfigFile.ini
```

This script create Beacon Friendly Format (BFF) files compatible to the Reference Implementation BeaconV2 API.

## Light a Beacon (beta version)

For creating a BeaconV2 working instance we are going to use the Reference Implementation developed at the Centre for Genomic Regulation (CRG). The following code is based on this [repo](https://github.com/MauricioMoldes/deploy_beacon_v2_reference_implementation).

### Requirements

* Open ports 5050, 8080, 8081, 27017 
* Install <a href="https://docs.docker.com/compose/install/" target="_blank">docker-compose</a>
* Install <a href="https://www.mongodb.com/docs/database-tools/installation/installation/" target="_blank">mongoimport</a>. Or run `sudo apt install mongodb-org-tools`.

### Deploying the beacon

- Clone API repo:

```
git clone https://github.com/MauricioMoldes/beacon2-ri-api
cd beacon2-ri-api/deploy
```

- Start MongoDB container:

```
docker-compose up -d db
```

- Import the BFF data created to MongoDB:

```
mongoimport --jsonArray --uri "mongodb://root:example@127.0.0.1:27017/beacon?authSource=admin" --file /path/to/biosamples.json --collection biosamples
mongoimport --jsonArray --uri "mongodb://root:example@127.0.0.1:27017/beacon?authSource=admin" --file /path/to/individuals.json --collection individuals
mongoimport --jsonArray --uri "mongodb://root:example@127.0.0.1:27017/beacon?authSource=admin" --file /path/to/genomicVariants.json --collection genomicVariations 
```

**Note**
Remember to put the correct path of your files in the command line.

- Start Beacon containers:

```
docker-compose up -d mongo-express
docker-compose up -d beacon
```

- Start Beacon UI container:

```
docker-compose up -d training-ui
```

### Usage

Access the beacon reference implementation on your localhost: 

 * http://localhost:5050/api/ - beacon-api
 * http://localhost:8080/ - training-ui
 * http://localhost:8081 - mongo-express
