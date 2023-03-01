
import uuid
import time

def createGenomicsFile(listGenomicData):
	
	listDictGenomics = []
	# Genomic Variants file
	for genomicData in listGenomicData:
		dictGenomicData = {}
		# Position property not in specification but needed for Beacon RI API
		dictGenomicData['position'] = {
			'start':[int(genomicData['startPosition'])],
			'startInteger':int(genomicData['startPosition']),
			'end':[int(genomicData['endPosition'])],
			'endInteger':int(genomicData['endPosition']),
			'refseqId': genomicData['chr'],
			'assemblyID': genomicData['ncbiBuild']
			}
		# Id creation and printing
		# TO DO: Separate caseLevelData.id, variantInternalId
		id = str(uuid.uuid1(clock_seq=int(time.time()*10000000))) # Create Unique Id based on the clock and hardware address
		dictGenomicData['variantInternalId'] = id
		dictGenomicData['caseLevelData'] = []
		dictCaseLevelData = {'individualId': genomicData['patientId'], 'biosamplelId': genomicData['sampleId']}
		if 'mutationStatus' in genomicData:
			alleleOrigin = {'alleleOrigin':{'label':genomicData['mutationStatus']}}
			dictCaseLevelData = { **dictCaseLevelData, **alleleOrigin}
		dictGenomicData['caseLevelData'].append(dictCaseLevelData)
		dictGenomicData['variation'] = {
				'alternateBases': genomicData['variantAllele'],
				'referenceBases': genomicData['referenceAllele'],
				'location':{
					'type':'SequenceLocation',
					'interval': {
						'type': 'SequenceInterval',
						'end': {
							'value':int(genomicData['startPosition']),
							'type':'Number'
						},
						'start':{
							'value': int(genomicData['endPosition']),
							'type': 'Number'
						}
					}
				}
			}
		if 'mutationType' in genomicData:
			dictGenomicData['variantLevelData'] ={'phenotypicEffects':[{'category':{'label':genomicData['mutationType']}}]}
		if 'proteinChange' in genomicData:
			dictGenomicData['identifiers'] = {'proteinHGVSIds': [genomicData['proteinChange']]}
		if 'entrezGeneId' in genomicData:
			dictGenomicData['molecularAttributes'] = {'geneIds': [genomicData['entrezGeneId']]}
		listDictGenomics.append(dictGenomicData)
	return listDictGenomics