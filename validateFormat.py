
# Libraries
import re
import datetime
import sys

def validateDateTime(dateText):
    try:
        datetime.datetime.fromisoformat(dateText)
    except ValueError:
        raise ValueError("Incorrect data format, should be the following attributes: year, month, day, hour, minute, second, microsecond, and tzinfo.")

def validateDate(dateText):
    try:
        datetime.date.fromisoformat(dateText)
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")

def validateTime(dateText):
    try:
        datetime.time.fromisoformat(dateText)
    except ValueError:
        raise ValueError("Incorrect data format, should be attributes: hour, minute, second, microsecond, and tzinfo.")

def validateMail(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if not re.fullmatch(regex, email):
        print("Invalid Email")

def validateURI(uri):
    pattern = "^https:\/\/[0-9A-z.]+.[0-9A-z.]+.[a-z]+$"
    if not re.match(pattern, uri):
        print("Incorret URI")

# Check all formats found in Beacon
def returnFormat(result, type):
    if type == "date-time":
        validateDateTime(result)
    elif type == "date":
        validateDate(result)
    elif type == "time":
        validateTime(result)
    elif type == "email":
        validateMail(result)
    elif type == "uri":
        validateURI(result)
    else:
        sys.exit(f"Format {type} not found")