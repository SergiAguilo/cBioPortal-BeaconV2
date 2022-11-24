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
def retrieveAPIData(configVariables, studyId, patientORsample):
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


def writeGenomicsFile(listGenomicData, outputFileGenomicVariants):
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
	# Write info to a file
	f = open(outputFileGenomicVariants, 'w')
	f.write(json.dumps(listDictGenomics, indent=1))
	f.close()

# Recursive function to add dot separated strings as dictionary
# Ex: sex.label = Male -> {"sex":{"label": "Male"}}
def add_branch(tree, vector, value):
	key = vector[0]
	if len(vector) ==0:
		tree[key] = value
		return tree
	tree[key] = value \
		if len(vector) == 1 \
		else add_branch(tree[key] if key in tree else {},
						vector[1:],
						value)
	return tree

def writeIndividualFile(listPatientData, outputFileIndividuals):
	listIndividualData = []
	for individualData in listPatientData:
		dictIndividualData = {}
		for patientVariable in individualData:
			if patientVariable == 'patientId':
				dictIndividualData['id'] = individualData['patientId']
			else:

				dictIndividualData = add_branch(dictIndividualData, patientVariable.split("."), individualData[patientVariable])

		listIndividualData.append(dictIndividualData)
		f = open(outputFileIndividuals, 'w')
		f.write(json.dumps(listIndividualData, indent=1))
		f.close()


def writeSampleFile(listSampleData, dictMappingPatientSample, outputFileBiosample):
	listDictSampleData = []
	for sampleData in listSampleData:
		dictSampleData = {}
		for sampleVariable in sampleData:
			if sampleVariable == 'patientId':
				dictSampleData['id'] = sampleData['sampleId']
				dictSampleData['individualId'] = dictMappingPatientSample[sampleData['sampleId']]
			else:
				dictSampleData = add_branch(dictSampleData, sampleVariable.split("."), sampleData[sampleVariable])
		listDictSampleData.append(dictSampleData)
	f = open(outputFileBiosample, 'w')
	f.write(json.dumps(listDictSampleData, indent=1))
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
	# Extract Patient Data
	if dictConfig['Patient Data']:
		listPatientData, _ = retrieveAPIData(dictConfig['Patient Data'], studyId, 'patients')
	# Extract Sample Data
	if dictConfig['Sample Data']:
		listSampleData, dictMappingPatientSample = retrieveAPIData(dictConfig['Sample Data'], studyId, 'samples')
	# Extract Genomic Variants Data
	listGenomicData = retrieveGenomicVariants(studyId)
	writeGenomicsFile(listGenomicData, outputFileGenomicVariants)
	writeSampleFile(listSampleData, dictMappingPatientSample, outputFileBiosample)
	writeIndividualFile(listPatientData, outputFileIndividuals)


if __name__ == '__main__':
    main()