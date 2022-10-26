import json
from random import sample
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
	
	dictMappingPatientSample = {}
	if patientORsample =='samples':
		for sampleEntry in samplePatientIdsJson:
			dictMappingPatientSample[sampleEntry['sampleId']] = [sampleEntry['patientId']]
	
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
	# f = open(outputFile, 'w')
	# f.write(str(listSamplePatients))
	# f.close()
	return listSamplePatients, dictMappingPatientSample


# Extract Mutation data
def retrieveGenomicVariants(studyId):
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
				if not infoGenomicVariant in molecularData:
					continue
				dictGenomicVariant[infoGenomicVariant] = molecularData[infoGenomicVariant] # Store the info in the dict
			listGenomicVariants.append(dictGenomicVariant)
	return listGenomicVariants


def writeGenomicsFile(listGenomicData):
	listDictGenomics = []
	# Genomic Variants file
	for genomicData in listGenomicData:
		dictGenomicData = {}
		dictGenomicData['_position'] = {'start':[int(genomicData['startPosition'])],
			 'startInteger':int(genomicData['startPosition']),
			 'end':[int(genomicData['endPosition'])],
			 'endInteger':int(genomicData['endPosition']),
			 'refseqId': genomicData['chr'],
			 'assemblyID': genomicData['ncbiBuild']}
		dictGenomicData['caseLevelData'] = [{'individualId': genomicData['patientId'], 'biosamplelId': genomicData['sampleId']}]
		if 'mutationStatus' in genomicData:
			dictGenomicData['caseLevelData'] += [{'alleleOrigin':{'label':genomicData['mutationStatus']}}]

		dictGenomicData['variation'] = {'alternateBases': genomicData['variantAllele'],
			'referenceBases': genomicData['referenceAllele'],
			'location':{'interval': {'end': {'value':int(genomicData['startPosition']), 'type':'Number'},
			 	'start':{'value': int(genomicData['endPosition']), 'type': 'Number'}}}
			 }
		if 'mutationType' in genomicData:
			dictGenomicData['variantLevelData'] = {'phenotypicEffects': {'category': genomicData['mutationType']}}
		if 'proteinChange' in genomicData:
			dictGenomicData['proteinHGVSIds'] = [genomicData['proteinChange']]
		if 'entrezGeneId' in genomicData:
			dictGenomicData['molecularAttributes'] = {'geneIds': [genomicData['entrezGeneId']]}
		listDictGenomics.append(dictGenomicData)
	# for patientData in listPatientData:
	# 	patientId = dictMappingPatientSample[patientData['patientId']]
	# Write info to a file
	f = open('genomic.json', 'w')
	f.write(json.dumps(listDictGenomics, indent=1))
	f.close()

def writeIndividualSampleFile(listPatientData, listSampleData, dictMappingPatientSample):
	listDictSampleData = []
	dictDiseasePatient = {}
	for sampleData in listSampleData:
		dictSampleData = {}
		dictSampleData['id'] = sampleData['sampleId']
		dictSampleData['individualId'] = dictMappingPatientSample[sampleData['sampleId']]
		dictSampleData['PhenotypicFeature'] = {'featureType':{'label': sampleData['phenotypicfeature']}}
		dictSampleData['tumorProgression'] = {'label': sampleData['tumorprogression']}
		dictDiseasePatient[sampleData['sampleId']] = sampleData['phenotypicfeature']
		listDictSampleData.append(dictSampleData)
	f = open('biosample.json', 'w')
	f.write(json.dumps(listDictSampleData, indent=1))
	f.close()

	listIndividualData = []
	for individualData in listPatientData:
		dictIndividualData = {}
		dictIndividualData['id'] = individualData['patientId']

		dictIndividualData['sex'] = {'label': individualData['sex']}
		if 'ethnicity' in individualData:
			dictIndividualData['ethnicity'] = {'label': individualData['ethnicity']}
		if 'age' in individualData:
			dictIndividualData['disease'] = {'ageOfOnset': {'Age': individualData['age']},'diseaseCode':{'label': dictDiseasePatient[individualData['patientId']]}}
		listIndividualData.append(dictIndividualData)
	f = open('individual.json', 'w')
	f.write(json.dumps(listIndividualData, indent=1))
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
	listPatientData = []
	listSampleData = []
	listGenomicData = []
	dictMappingPatientSample = {}
	# # Extract Patient Data
	if dictConfig['Patient Data']:
		listPatientData, _ = retrieveAPIData(dictConfig['Patient Data'], studyId, 'patients', outputFileIndividuals)
	# # Extract Sample Data
	if dictConfig['Sample Data']:
		listSampleData, dictMappingPatientSample = retrieveAPIData(dictConfig['Sample Data'], studyId, 'samples', outputFileBiosample)
	# Extract Genomic Variants Data
	# listGenomicData = retrieveGenomicVariants(studyId)
	# writeGenomicsFile( listGenomicData)
	writeIndividualSampleFile(listPatientData, listSampleData, dictMappingPatientSample)


if __name__ == '__main__':
    main()