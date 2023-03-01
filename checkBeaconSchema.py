
import re
from validateFormat import returnFormat

# Check with OneOf belongs to the variable
def checkOneOf(variable, schema, counterVariable):
    for oneOf in schema:
        if variable[counterVariable] in oneOf["properties"]:
            return oneOf["properties"]

# Recursive function to parse the schema to find the type of the variables
def checkFormatSchema(variable, schema, typeList, formatDict, counterVariable, depthVariable):
    if "oneOf" in schema:
        schemaPath = checkOneOf(variable, schema["oneOf"],counterVariable)
        typeList.append(schemaPath[variable[counterVariable]]["type"])
        counterVariable += 1
    # If all the variables are parsed, return the list
    if counterVariable == depthVariable:
        return typeList
    else:
        # Depend on the type of variable, the schema will be parsed differently
        if len(typeList):
            if typeList[-1] == "array":
                schemaPath = schema["items"]["properties"]
            else:
                schemaPath = schema["properties"]
        else:
            schemaPath = schema["properties"]
    # Check if variable inside the part of the schema
    for propertyKey, propertyValue in schemaPath.items():
        if variable[counterVariable] in propertyKey:
            typeList.append(propertyValue["type"])
            # Check format (Ex: Date, Mail, regex, etc)
            if "format" in propertyValue:
                formatDict[counterVariable] = propertyValue["format"]
            # Recursive function to enter to the subschema of the schema
            typeList = checkFormatSchema(variable, schemaPath[variable[counterVariable]],
                                         typeList, formatDict, counterVariable + 1,depthVariable)
            return typeList

# Check if string is in ISO 8601 format, "P"+string+"Y"
# If it is, do nothing
# Else, convert the string to ISO 8601 format
def checkISO8601Duration(result):
    pattern = "^P(?!$)(\d+(?:\.\d+)?Y)?(\d+(?:\.\d+)?M)?(\d+(?:\.\d+)?W)?(\d+(?:\.\d+)?D)?(T(?=\d)(\d+(?:\.\d+)?H)?(\d+(?:\.\d+)?M)?(\d+(?:\.\d+)?S)?)?$"
    if re.match(pattern, result):
        return result
    if result.isdigit():
        return f"P{result}Y"

# Format the variables regarding its type and format
def createOutputVariable(variable, result, typeList, formatDict):
    outDict = {}
    for numVar in reversed(range(len(variable))):
        if typeList[numVar] == "array":
            outDict = {variable[numVar]: [outDict]}
        elif typeList[numVar] == "object":
            outDict = {variable[numVar]:outDict}
        elif typeList[numVar] == "string":
            if numVar in formatDict:
                # Check if the format is correct
                returnFormat(result, formatDict[numVar])
            # If variables is iso8601duration, we convert the strig to "P"+result+"Y" to match ISO 8601 format
            if variable[numVar]=="iso8601duration":
                result = checkISO8601Duration(result)
            outDict = {variable[numVar]:result}
        elif typeList[numVar] == "number" or typeList[numVar] == "integer":
            outDict = {variable[numVar]:int(result)}
        elif typeList[numVar] == "boolean":
            outDict = {variable[numVar]:result.lower()}     # Convert possible string "True" to json boolean "true"
    return outDict

# Function to check variables to Beacon Schema
# Then, the variables will be format in order to match the specification
# Ex: If sex is type:Object, it'll be represented with {}.
# If PhenotypicFeatures is array, it'll be represented with [].
def checkSchema(listData, schema):
    outputBeacon = []       # Init final list
    for entry in listData: # For all the entries in the 
        entryDict = {}
        # Check if variables match the schema and format them in BFF
        for variable,result in entry.items():
            variable = variable.split('.')      # Split subproperties
            typeList = []                       # Init list to know which type is each property (Ex: Object, array, string, etc.)
            formatDict = {}                     # Store variable with format (Ex: format:"datetime") with its position
            depthVariable = len(variable)
            # Check the type and format of the property and subproperties (if any)
            typeList = checkFormatSchema(variable, schema, typeList, formatDict, 0, depthVariable)
            # Retrieve the variables with their proper type and format
            outputVariableBeacon = createOutputVariable(variable, result, typeList, formatDict)
            entryDict.update(outputVariableBeacon)
        outputBeacon.append(entryDict)
    return outputBeacon