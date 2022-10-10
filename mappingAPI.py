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

def retrieveAPIData(configVariables, studyId, patientORsample, outputFile):
	if patientORsample =='patients':
		patientORsampleId = 'patientId'
	else:
		patientORsampleId = 'sampleId'
	samplePatientIdsJson = f"https://www.cbioportal.org/api/studies/{studyId}/{patientORsample}"
	response = urlopen(samplePatientIdsJson)
	samplePatientIdsJson = json.loads(response.read())
	listSamplePatients = []
	for samplePatientId in samplePatientIdsJson:
		samplePatientId = samplePatientId[patientORsampleId]
		dictSamplePatientId = {patientORsampleId: samplePatientId}
		for configVariable in configVariables:
			urlData=f"https://www.cbioportal.org/api/studies/{studyId}/{patientORsample}/{samplePatientId}/clinical-data?attributeId={configVariables[configVariable]}"
			response = urlopen(urlData)
			dataJson = json.loads(response.read())
			if not dataJson:
				continue
			dictSamplePatientId[configVariable] = dataJson[0]["value"]
		listSamplePatients.append(dictSamplePatientId)
	f = open(outputFile, 'w')
	f.write(str(listSamplePatients))
	f.close()

def retrieveGenomicVariants(studyId, outputFile):
	listInfoGenomicVariants = ['mutationType', 'proteinChange', 'ncbiBuild',
	 'chr', 'startPosition', 'endPosition', 'entrezGeneId', 'mutationStatus',
	 'referenceAllele', 'variantAllele', 'sampleId', 'patientId']
	listGenomicVariants = []
	listMolecularProfiles = f"https://www.cbioportal.org/api/studies/{studyId}/molecular-profiles"
	response = urlopen(listMolecularProfiles)
	listMolecularProfiles = json.loads(response.read())
	for molecularProfiles in listMolecularProfiles:
		if molecularProfiles['molecularAlterationType'] != 'MUTATION_EXTENDED':
			continue
		molecularProfileId = molecularProfiles['molecularProfileId']
	listSampleID = f"https://www.cbioportal.org/api/studies/{studyId}/sample-lists"
	response = urlopen(listSampleID)
	listSampleID = json.loads(response.read())
	for sampleID in listSampleID:
		if sampleID['category'] != 'all_cases_with_mutation_data':
			continue
		sampleID=sampleID["sampleListId"]
		listMolecularData = f"https://www.cbioportal.org/api/molecular-profiles/{molecularProfileId}/mutations?sampleListId={sampleID}"
		response = urlopen(listMolecularData)
		listMolecularData = json.loads(response.read())
		for molecularData in listMolecularData:
			dictGenomicVariant = {}
			for infoGenomicVariant in listInfoGenomicVariants:
				dictGenomicVariant[infoGenomicVariant] = molecularData[infoGenomicVariant]
			listGenomicVariants.append(dictGenomicVariant)
	f = open(outputFile, 'w')
	f.write(str(listGenomicVariants))
	f.close()

def main():
	dictConfig = readIni(configPath)
	studyId = dictConfig['Main Config']['studyid']
	outputFileIndividuals = dictConfig['Main Config']['outputindividuals']
	outputFileBiosample = dictConfig['Main Config']['outputbiosamples']
	outputFileGenomicVariants = dictConfig['Main Config']['outputgenomicvariants']

	if dictConfig['Patient Data']:
		retrieveAPIData(dictConfig['Patient Data'], studyId, 'patients', outputFileIndividuals)

	if dictConfig['Sample Data']:
		retrieveAPIData(dictConfig['Sample Data'], studyId, 'samples', outputFileBiosample)

	retrieveGenomicVariants(studyId, outputFileGenomicVariants)


if __name__ == '__main__':
    main()