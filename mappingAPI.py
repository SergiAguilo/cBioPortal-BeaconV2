import json
import sys
from urllib.request import urlopen
import configparser

configPath=sys.argv[1]

# Read config.ini
def readIni(configPath):
	config = configparser.ConfigParser()
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

# Extract Clinical Data from Patients and Samples
def retrieveAPIData(configVariables, studyId, patientORsample, outputFile):
	if patientORsample =='patients':
		patientORsampleId = 'patientId'
	else:
		patientORsampleId = 'sampleId'
	# List of Ids of the patients and samples
	samplePatientIdsJson = f"https://www.cbioportal.org/api/studies/{studyId}/{patientORsample}"
	response = urlopen(samplePatientIdsJson)
	samplePatientIdsJson = json.loads(response.read())
	# Extract Sample or Patient data
	listSamplePatients = [] # List of all patient or sample data
	for samplePatientId in samplePatientIdsJson:					# For each sampleId or patientId
		samplePatientId = samplePatientId[patientORsampleId]
		dictSamplePatientId = {patientORsampleId: samplePatientId}	# Dict for storing data of each entry
		for configVariable in configVariables:						# For each variable in the config.ini file
			# API search
			urlData=f"https://www.cbioportal.org/api/studies/{studyId}/{patientORsample}/{samplePatientId}/clinical-data?attributeId={configVariables[configVariable]}"
			response = urlopen(urlData)
			dataJson = json.loads(response.read())
			if not dataJson:	# If variable do not have any values, remove it
				continue
			dictSamplePatientId[configVariable] = dataJson[0]["value"]
		listSamplePatients.append(dictSamplePatientId)
	# Write info to a file
	f = open(outputFile, 'w')
	f.write(str(listSamplePatients))
	f.close()

# Extract Mutation data
def retrieveGenomicVariants(studyId, outputFile):
	# List of variables used in Beacon
	listInfoGenomicVariants = ['mutationType', 'proteinChange', 'ncbiBuild',
	 'chr', 'startPosition', 'endPosition', 'entrezGeneId', 'mutationStatus',
	 'referenceAllele', 'variantAllele', 'sampleId', 'patientId']
	listGenomicVariants = []	# List to store all the information
	# API to find the Molecular Profile ID
	listMolecularProfiles = f"https://www.cbioportal.org/api/studies/{studyId}/molecular-profiles"
	response = urlopen(listMolecularProfiles)
	listMolecularProfiles = json.loads(response.read())
	# For now, we are only interested in the Mutation Data
	# Take the object with MUTATION_EXTENDED as Molecular Alteration Type
	for molecularProfiles in listMolecularProfiles:
		if molecularProfiles['molecularAlterationType'] != 'MUTATION_EXTENDED':
			continue
		molecularProfileId = molecularProfiles['molecularProfileId']
	# API to find the sample list related with mutation data
	listSampleID = f"https://www.cbioportal.org/api/studies/{studyId}/sample-lists"
	response = urlopen(listSampleID)
	listSampleID = json.loads(response.read())
	# Take the sampleList Id for the mutation data -> Category = all_cases_with_mutation_data
	for sampleID in listSampleID:
		if sampleID['category'] != 'all_cases_with_mutation_data':
			continue
		sampleID=sampleID["sampleListId"]
		# After having the Molecular Profile Id and sampleList Id we can query for genomics variants data
		listMolecularData = f"https://www.cbioportal.org/api/molecular-profiles/{molecularProfileId}/mutations?sampleListId={sampleID}"
		response = urlopen(listMolecularData)
		listMolecularData = json.loads(response.read())
		for molecularData in listMolecularData:		# For all the entries having a mutation
			dictGenomicVariant = {}					# Dict for storing data of each mutation object
			for infoGenomicVariant in listInfoGenomicVariants:	# For all variables that can map with Beacon
				dictGenomicVariant[infoGenomicVariant] = molecularData[infoGenomicVariant] # Store the info in the dict
			listGenomicVariants.append(dictGenomicVariant)
	# Write info to a file
	f = open(outputFile, 'w')
	f.write(str(listGenomicVariants))
	f.close()

def main():
	# Read config file
	dictConfig = readIni(configPath)
	# Study Id
	studyId = dictConfig['Main Config']['studyid']
	# Output Files
	outputFileIndividuals = dictConfig['Main Config']['outputindividuals']
	outputFileBiosample = dictConfig['Main Config']['outputbiosamples']
	outputFileGenomicVariants = dictConfig['Main Config']['outputgenomicvariants']

	# Extract Patient Data
	if dictConfig['Patient Data']:
		retrieveAPIData(dictConfig['Patient Data'], studyId, 'patients', outputFileIndividuals)
	
	# Extract Sample Data
	if dictConfig['Sample Data']:
		retrieveAPIData(dictConfig['Sample Data'], studyId, 'samples', outputFileBiosample)
	
	# Extract Genomic Variants Data
	retrieveGenomicVariants(studyId, outputFileGenomicVariants)


if __name__ == '__main__':
    main()