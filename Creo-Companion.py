#Code is no longer maintained

import creopyson #Module used to interface and comunicate with Creo Parametric
import os #  
import sys
import getpass
import time
from subprocess import Popen
from collections import Counter
from rich import print
from rich.console import Console
from rich.progress import track
import textwrap

con = Console()

c = creopyson.Client()

def end():
    print('Exiting program now')
    sys.exit()

def find_files(filename):
    cwd = os.getcwd()
    print(cwd)
    result = []
    # Wlaking top-down from the root
    for root, dir, files in os.walk(cwd):
        if filename in files:
            result.append(os.path.join(root, filename))
            return result
    return False

def tryagainorexit(prompt, retries=4, reminder='Please try again that was not a valid entry!'):
    while True:
        ok = input(prompt)
        if ok.lower() in ('y', 'ye', 'yes'):
            return True
        elif ok.lower() in ('n', 'no'):
            return False
        else:
            sys.exit()
            #retries = retries - 1
        if retries < 0:
            raise ValueError('invalid user response')
        print(reminder)

def entertocontinue(msg):
    print(msg)
    input('Press enter to continue')

def entertoexit(msg):
    print(msg)
    input('Press enter to exit:')
    sys.exit()

def startServer():
    cwd = os.getcwd()
    directories = cwd.split('\\')
    user = "\\".join(directories[0:3])
    desktop = user + "\\Desktop"
    os.chdir(desktop)
    serverlocation = find_files('creoson_run.bat')
    if serverlocation == False:
        print('Failed to start server')
        return False
    serverlocation = os.path.dirname(serverlocation[0])
    os.chdir(serverlocation)
    Popen('creoson_run.bat')
      
def connect():
    cresonrunflag = 0
    while  cresonrunflag <= 1:

        print('[yellow]\nConnecting to Creoson server...[/yellow]')
        try:
            c.connect()
            print("[green]Connected!\n[/green]")
            cresonrunflag = 2
        except ConnectionError:
            print('[red]Creoson server is not running[/red]')
            print('Trying to start server')
            if startServer() == False:              
                print('Please make sure the server is running and try again.')
                cresonrunflag = tryagainorexit('y/yes to try again Enter to exit:')
    
    while(c.is_creo_running() == False):
            print("Creo is not running, make sure creo is running and the creoson server is setup corretly")
            tryagainorexit('y/yes to try again Enter to exit:')
    try:
        print('Your current working directory: [green]{}[/green]'.format(c.creo_pwd()))
    except:
        print('[red]Unable to get current working directoy[/red]')
    try:
        print('Your current workspace: [cyan]{}[/cyan]'.format(c.windchill_get_workspace()))
    except RuntimeError:
        print('[red]\nYou are not connected/activated on any Windchill workspace![/red]')

def grabFiles():

    print("[yellow]Grabbing workspace files...[/yellow]")
    workspaceFiles = c.windchill_list_workspace_files()  
    print("[green]Files Stored[/green]")
    return workspaceFiles


def filterParts(filterstr):
    filtered = filter(lambda x:filterstr in x , files)
    return list(filtered)

def topWords():
    
    splitFiles = []
    for items in workspacefiles:
        splitFiles.append(items.split('_')) 
    count = Counter(sublist[0] for sublist in splitFiles)
    most_common = count.most_common(2)
    topWords = []
    for items in most_common:
        topWords.append(items[0])
    return(topWords)

def paramEditor():
    
    topWordlist = topWords()
    topWord = topWordlist[0]

    usetopword = con.input("The most common set of caracters in the workspace are [blue]{}[/blue] do the files you want to change contain these characters? Enter to continue or enter n to chagne: ".format(topWord))
    if  usetopword.lower() != "n":
        filestochange = topWord
    else:
        print("What are the common characters of the parts you want to change? Typically this is the tool number at the beginning of a part:")
        filestochange = input("")

    manual_model = input("Press enter to auto find parameters or enter \"n\" to manualy open and activate a model: ")

    print("\n")

    flag1 = 0

    if manual_model.lower() != "n":
        print("Opening and searching creo files to find partparameters...")
        for files in workspacefiles:
            if (files.find(filestochange) > -1):
                flag1 = 0
                c.file_open(file_=files)
                partparameters = (c.parameter_list())
                for parameters in partparameters:
                    if parameters['name'] in ["TOOL_NUMBER","DYNACAST_PART_NUMBER", "PROJECT_NO"]:
                        flag1 += 1
                    if flag1 >=3:
                        break
            if flag1 >=3:
                break
    else:
        input('Open up and activate a model, then press enter to continue')
        partparameters = (c.parameter_list())
        flag1 = 3


    parameterlist = []
    parameterlistfiltered = []

    if flag1 >= 3:
        for parameters in partparameters:
            parameterlist.append(parameters['name'])

        for params in parameterlist:
            if params.find("PTC") == -1:
                if params.find("PROI_") == -1:
                    parameterlistfiltered.append(params)
        
    else:
        print("No parameters found in", c.file_get_active()['file'])
        end()

    listnumber = 0
    parameter = "none"
    newparametervalue = "none"

    def listandchange():
        for x in range(len(parameterlistfiltered)):
            print (x, parameterlistfiltered[x])
        listnumber = int(input("Pick the number of the parameter you want to change:"))
        parameter = parameterlistfiltered[listnumber]
        print("what do you want to change the", parameter, "parameter to?")
        newparametervalue = input("")

        for files in workspacefiles:
            if (files.find(filestochange) > -1):
                if c.parameter_exists(parameter):
                    try:
                        c.parameter_set(parameter , newparametervalue, files)
                        print("[cyan]parameter[/cyan] {} [red]changed[/red] in [cyan]{}[/cyan]".format(parameter, files))
                    except:
                        print('Unable to change', files)

    def repeat():
        repeatflag = tryagainorexit("Do you want to repeat with a different parameter? y or n:")
        #print(repeatflag)
        while repeatflag == True:
            listandchange()
            repeatflag = tryagainorexit("Do you want to repeat with a different parameter? y or n:")    

    listandchange()
    repeat()

    entertoexit("Finished")

def listDims():
    dims = c.dimension_list_detail()
 
    print(c.familytable_list())

print(textwrap.fill(
    '[bright_blue]This program was made by Nathan Moore for use at Dynacast Germantown [/bright_blue]', width=120))

functionList = {
    1: paramEditor
}

connect()

choice = print("what you you like to do, below are your choices\n")

print("1    Edit Parameters")
print('')
choice = int(input(":"))


workspacefiles = grabFiles()

functionList[choice]()