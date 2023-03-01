
# Import Libraries
import sys
import configparser
import os
from jsonref import replace_refs
import json

# Import functions from the modular files
from retrievecBioPortalAPI import retrieveAPIData, retrieveGenomicVariants
from checkBeaconSchema import checkSchema
from outputGenomicsData import createGenomicsFile

# Configuration file as first argument
configPath=sys.argv[1]

# Read config.ini
def readIni(configPath):
	config = configparser.ConfigParser()
	config.optionxform=str

	config.read(configPath)
	dictConfig = {}
	for section in config.sections():
		dictConfig[section] = {}
		for key in config[section]:
			# Avoid empty variables
			if not config[section][key]:
				continue
			# Write config values to the dict
			dictConfig[section][key] = config[section][key]
	return dictConfig

# Store Default schema of the model and all its references
def readSchema(pathSchema):
    # Get Folder
    pathToIndividualSchemaFolder = os.path.dirname(pathSchema) + "/"
    print("Reading schema of this path:", pathToIndividualSchemaFolder)
    f = open(pathSchema)
    data = json.load(f)
    # Retrieve all the $ref of the schema in a single file (in this case the fullSchema variable)
    fullSchema=replace_refs(data,base_uri="file://" + pathToIndividualSchemaFolder)
    return fullSchema

def main():
    # Read config file
	dictConfig = readIni(configPath)
	# Study Id
	studyId = dictConfig['Main Config']['studyId']
	# Output Files
	outputFileIndividuals = dictConfig['Main Config']['outputIndividuals']
	outputFileBiosample = dictConfig['Main Config']['outputBiosamples']
	outputFileGenomicVariants = dictConfig['Main Config']['outputGenomicVariants']
	# Schema Files
	pathIndividualSchema = dictConfig['Main Config']['pathIndividualSchema']
	pathBiosampleSchema = dictConfig['Main Config']['pathBiosampleSchema']
    # Initialize lists and dictionary that store the data
	listPatientData = []
	listSampleData = []
	listGenomicData = []
	
    # Extract data from cBioPortal API
    # If Patient data, retrieve its data from cBioPortal
	if dictConfig['Patient Data']:
		print('Retrieving Patient Data')
		listPatientData = retrieveAPIData(dictConfig['Patient Data'], studyId, 'patients')
	# If Sample data, retrieve its data from cBioPortal
	if dictConfig['Sample Data']:
		print('Retrieving Sample Data')
		listSampleData = retrieveAPIData(dictConfig['Sample Data'], studyId, 'samples')
	print('Retrieving Genomic Variants Data')
	# List of variables in cBioPortal that can be mapped to Beacon
	listInfoGenomicVariants = ['mutationType', 'proteinChange', 'ncbiBuild',
	 'chr', 'startPosition', 'endPosition', 'entrezGeneId', 'mutationStatus',
	 'referenceAllele', 'variantAllele', 'sampleId', 'patientId']
	listGenomicData = retrieveGenomicVariants(studyId, listInfoGenomicVariants)
	
	# Check Schema individuals and format its output
	schemaIndividuals = readSchema(pathIndividualSchema)
	individualOutput = checkSchema(listPatientData, schemaIndividuals)
	f = open(outputFileIndividuals, 'w')
	f.write(json.dumps(individualOutput, indent=1))
	f.close()
    # Check Schema biosamples and format its output
	schemaBiosamples = readSchema(pathBiosampleSchema)
	biosampleOutput = checkSchema(listSampleData, schemaBiosamples)
	f = open(outputFileBiosample, 'w')
	f.write(json.dumps(biosampleOutput, indent=1))
	f.close()
	
	# Create GenomicVariants file
	listDictGenomics = createGenomicsFile(listGenomicData)
	f = open(outputFileGenomicVariants, 'w')
	f.write(json.dumps(listDictGenomics, indent=1))
	f.close()


if __name__ == '__main__':
    main()