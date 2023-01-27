import subprocess
import datetime
import sys
import os
import boto3
import colorama

from botocore.exceptions import ClientError
from colorama import Fore, Style

def printErr(err_msg):
    print("[", end="")
    print(Fore.RED + err_msg, end="")
    print(Style.RESET_ALL, end="")
    print("]", end="")

def printSuc():
    print("[", end="")
    print(Fore.GREEN + "Success", end="")
    print(Style.RESET_ALL, end="")
    print("]", end="")

directory = "C:\\Users\\Irek\\Documents\\"
sql_directory = "C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin"
date = datetime.date.today()
date = date.strftime("%Y-%m-%d")
filename = "Backup_" + date + ".sql"
args = [
    sql_directory + "\\mysqldump.exe",
    "-u",
    "root",
    "-proot",
    "main_db",
    "--result-file=C:\\Users\\Irek\\Documents\\" + filename]
filename_arr = [None]

def rotateBackups(filename_arr):
    len = getListLen()
    if len < 30:
        for file in filename_arr:
            print(file.split("_")[1])


def getListLen():
    i = 0
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and filename.startswith("Backup"):
            i += 1
    return i

def createList(len):
    arr = [None] * len
    i = 0
    for filename in os.listdir(directory):
        if filename.startswith("Backup"):
            arr[i] = filename
            i += 1
    return arr

try:
    check = subprocess.run(args)
    if check.returncode != 0:
        raise Exception("The mysqldump.exe script failed")
    else:
        printSuc()
        print(" mysqldump.exe successfuly created backup file")
except:
    printErr("Error")
    print(" mysqldump.exe script failed")
print(getListLen())
filename_arr = createList(getListLen())
rotateBackups(filename_arr)
print(filename_arr[0])
print(filename_arr[1])
print(filename_arr[2])


# SENDER = "Matt Spiewak <sys-mail.no-reply@apps.cesamseed.com"

# RECIPIENT = "matt.s92@hotmail.fr"

# AWS_REGION = "eu-west-3"

# SUBJECT = "This is a test fam"

# BODY_TEXT = ("Amazon SES Test (Python)\r\n"
#              "This email was sent with Amazon SES using the "
#              "AWS SDK for Python (Boto).")

# CHARSET = "UTF-8"

# client = boto3.client('ses', region_name=AWS_REGION)

# try:
#     response = client.send_email(
#         Destination={
#             'ToAddresses': [
#                 RECIPIENT,
#             ],
#         },
#         Message={
#             'Body': {
#                 'Text': {
#                     'Charset': CHARSET,
#                     'Data': BODY_TEXT,
#                 },
#             },
#             'Subject': {
#                 'Charset': CHARSET,
#                 'Data': SUBJECT,
#             },
#         },
#         Source=SENDER,
#     )
# except ClientError as e:
#     print(e.response['Error']['Message'])
# else:
#     print("All good")