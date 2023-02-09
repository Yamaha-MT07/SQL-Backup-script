import subprocess
import datetime
import logging
import sys
import os
import ssl

from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from colorama import Fore, Style
from tkinter.filedialog import askdirectory
from configparser import ConfigParser
from os.path import exists

logging.basicConfig(level=logging.DEBUG, filename="app.log", filemode="a", format="%(asctime)s %(message)s", datefmt="%Y-%m-%d | %H:%M:%S |")

def printErr(err_msg):
    print("[", end="")
    print(Fore.RED + "Error", end="")
    print(Style.RESET_ALL, end="")
    print("] ", end="")
    print(err_msg)
    return ("[Error] " + err_msg)

def printSuc(msg):
    print("[", end="")
    print(Fore.GREEN + "Success", end="")
    print(Style.RESET_ALL, end="")
    print("] ", end="")
    print(msg)
    return ("[Success] " + msg)

def printInfo(msg):
    print("[", end="")
    print(Fore.BLUE + "Info", end="")
    print(Style.RESET_ALL, end="")
    print("] ", end="")
    print(msg)
    return ("[Info] " + msg)

def printWarn(msg):
    print("[", end="")
    print(Fore.YELLOW + "Warning", end="")
    print(Style.RESET_ALL, end="")
    print("] ", end="")
    print(msg)
    return ("[Warning] " + msg)

def printBackupList(filename_arr):
    logging.info(printInfo("Current backups:"))
    for backup in filename_arr:
        logging.info(printInfo(backup))

def sendEmail(message):
    try:
        file = 'config.ini'
        config = ConfigParser()
        config.read(file)

        host = "email-smtp.eu-west-3.amazonaws.com"
        sender = "sys-mail.no-reply@apps.cesamseed.com"
        user = os.environ["AWS_USER_ID"]
        password = os.environ["AWS_PASSWORD"]
        receivers = config["EMAILS"]

        context = ssl.create_default_context()

        with SMTP(host, 587) as server :
            server.starttls(context=context)
            server.login(user=user, password=password)
            for index in receivers:
                server.sendmail(sender, receivers[index], message.as_string())
    except:
        logging.error(printErr("An error occured during the communication with the smtp server"))
    else:
        logging.info(printSuc("Email successfully sent"))

def sendErrEmail(reason):
    message = MIMEMultipart()
    message["Subject"] = "Cesadmin backup report"
    body = "The script failed to execute the backup, manual intervention required.<br><br>Details:<br>" + reason + "<br><br>This email has been generated automatically, please do not reply to it."

    message.attach(MIMEText(body, "html"))
    sendEmail(message)

def sendSucEmail(details):
    message = MIMEMultipart()
    message["Subject"] = "Cesadmin backup report"
    body = "The script has executed the backup, nothing to report.<br><br>Details:<br>" + details + "<br><br>This email has been generated automatically, please do not reply to it."

    message.attach(MIMEText(body, "html"))
    sendEmail(message)

def configureMysqlCredentials(sql_directory, username):
    args = [
        sql_directory + "\\mysql_config_editor.exe",
        "set",
        "--user=" + username,
        "--password"]
    try:
        check = subprocess.run(args)
        if check.returncode != 0:
            raise Exception("The mysql_config_editor.exe script failed")
        else:
            logging.info(printSuc("Successfully updated MySQL credentials"))
    except:
        logging.error(printErr("The mysql_config_editor.exe script failed"))

def setCredentialsOption():
    if exists(".\\config.ini"):
        file = 'config.ini'
        config = ConfigParser()
        config.read(file)
        username = input("Enter your MySQL username: ")
        configureMysqlCredentials(config["DIRS"]["sql_directory"], username)
    else:
        logging.error(printErr("Config file doesn't exist"))
        exit()

def createConfigFile():
    config = ConfigParser()
    sql_directory = askdirectory(title='Please select your \'MySQL Server\' bin folder...')
    backup_directory = askdirectory(title='Please select the directory in which you want the backup files to be saved...')
    default_dir = askdirectory(title="Please select the directory in which you want the backup files to be saved if the backup server is unavailable or if an error occurs...")
    db_name = input("Enter the name of the database you want to create backups for: ")
    username = input("Enter your MySQL username: ")
    email = input("Enter an email adress that will be notified after the backups")

    if sql_directory == "" or backup_directory == "" or username == "" or db_name == "" or default_dir == "" or email == "":
        logging.error(printErr("Config file creation aborted..."))
        exit()

    configureMysqlCredentials(sql_directory, username)

    config["DIRS"] = {
        "sql_directory": sql_directory,
        "backup_directory": backup_directory + "/",
        "default_dir": default_dir + "/"
    }
    config["CREDENTIALS"] = {
        "username": username,
    }
    config["DB"] = {
        "db_name": db_name,
    }
    config["EMAILS"] = {
        "email1": email
    }
    with open("config.ini", "w") as f:
        config.write(f)

def checkConfigFile():
    file = 'config.ini'
    config = ConfigParser()
    config.read(file)
    os.environ["AWS_USER_ID"] = "AKIAVOSHXMGSJTPB5DVZ"
    os.environ["AWS_PASSWORD"] = "BAsJhT5pWT0Avz7glvCPIjiW74G8GtXGfHAahucqxSaz"

    for index in config:
        for element in config[index]:
            if config[index][element] == "":
                logging.error(printErr("Config file missing element \'" + element + "\' please fix it manually"))
                exit()
    logging.info(printSuc("Config file passed check"))

def getDateList(filename_arr):
    dateList = []
    for file in filename_arr:
        size = len(file)
        name = file[:size - 4]
        date = name.split("_")[1]
        dateList.append(datetime.datetime.strptime(date, '%Y-%m-%d').date())
    return dateList

def rotateBackups(filename_arr, directory):
    dateList = getDateList(filename_arr)
    oldestDate = datetime.date.today()
    for date in dateList:
        if date < oldestDate:
            oldestDate = date
    os.remove(directory + "Backup_" + oldestDate.strftime("%Y-%m-%d") + ".sql")
    logging.info(printSuc("Removed Backup_" + oldestDate.strftime("%Y-%m-%d") + ".sql because it was more than 30 days old"))

def getListLen(directory):
    i = 0
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and filename.startswith("Backup"):
            i += 1
    return i

def createList(len, directory):
    arr = [None] * len
    i = 0
    for filename in os.listdir(directory):
        if filename.startswith("Backup"):
            arr[i] = filename
            i += 1
    return arr

def cleanBackupList(directory, default_dir):
    if not exists(directory):
        directory = default_dir
    filename_arr = createList(getListLen(directory), directory)
    printBackupList(filename_arr)
    if getListLen(directory) > 30:
        rotateBackups(filename_arr, directory)

def runBackup(args, filename, directory, default_dir):
    warning = False
    if not exists(directory):
        warning = True
        directory = default_dir
        args[2] = "--result-file=" + directory + filename
        logging.warning(printWarn("Backup drive unavailable, defaulting to local... Check if the server/drive is online"))
    try:
        check = subprocess.run(args)
        if check.returncode != 0:
            os.remove(directory + filename)
            raise Exception("The mysqldump.exe script failed")
        else:
            logging.info(printSuc("mysqldump.exe successfully created backup file " + filename + " in " + directory))
            if warning == True:
                sendSucEmail("mysqldump.exe successfully created backup file " + filename + "<br>[Warning] Backup drive unavailable, defaulting to local... Check if the server/drive is online")
            else:
                sendSucEmail("mysqldump.exe successfully created backup file " + filename)
    except:
        logging.error(printErr("mysqldump.exe script failed"))
        sendErrEmail("[Error] mysqldump.exe script failed")

def startBackup():
    file = 'config.ini'
    config = ConfigParser()
    config.read(file)

    date = datetime.date.today().strftime("%Y-%m-%d")
    filename = "Backup_" + date + ".sql"

    directory = config["DIRS"]["backup_directory"]
    sql_directory = config["DIRS"]["sql_directory"]
    db_name = config["DB"]["db_name"]
    default_dir = config["DIRS"]["default_dir"]

    args = [
    sql_directory + "\\mysqldump.exe",
    db_name,
    "--result-file=" + directory + filename]

    runBackup(args, filename, directory, default_dir)
    cleanBackupList(directory, default_dir)

if len(sys.argv) == 2 and sys.argv[1] == "--set-credentials":
    setCredentialsOption()
    exit()
elif exists(".\\config.ini"):
    checkConfigFile()
else:
    logging.info(printInfo("Config file doesn't exist"))
    logging.info(printInfo("Manual configuration required"))
    createConfigFile()
    logging.info(printSuc("Config file 'config.ini' created successfully"))
startBackup()