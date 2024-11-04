import json
import os
import sys


printDetailedLogs = False

def printLog(log,args=None):
    if printDetailedLogs:
        print(log, args)

def checkIfSessionExists(session):
    printLog("Checking if session exists: ", session)
    if os.path.exists(session):
        return True
    else:
        return False


def getUserGroupDiff(srcSession, targetSession):
    print("Getting User Group  diff for source session: ", srcSession, " and target session: ", targetSession)
    srcUserGroupPath = srcSession + "/groups"
    targetUserGroupPath = targetSession + "/groups"
    allSrcGroups = os.listdir(srcUserGroupPath)
    allTargetGroups = os.listdir(targetUserGroupPath)

    clashingGroups = list(set(allSrcGroups) & set(allTargetGroups))
    printLog("Clashing groups: ", clashingGroups)
    return clashingGroups

def getAllUsers(session):
    printLog("Getting all users for session: ", session)
    userPath = session + "/groups/all_users"
    allUserJson  = json.load(open(userPath))
    allUserJson = allUserJson['members']

    allUsers = []
    for user in allUserJson:
        allUsers.append(user['userName'])
    return set(allUsers)

def getAllUserDiff(srcSession, targetSession):
    print("Getting all user diff for source session: ", srcSession, " and target session: ", targetSession)
    srcUsers = getAllUsers(srcSession)
    targetUsers = getAllUsers(targetSession)

    missingUsers = srcUsers - targetUsers
    printLog("Users missing in target session: ", missingUsers)
    return missingUsers

def findMissingUsersInGroup(srcSession, targetSession, group):
    printLog("Finding missing users in group: ", group)
    srcGroupPath = srcSession + "/groups/" + group
    targetGroupPath = targetSession + "/groups/" + group

    srcGroupJson = json.load(open(srcGroupPath))
    targetGroupJson = json.load(open(targetGroupPath))

    srcGroupUsers =  [i['userName'] for i in srcGroupJson['members']]
    targetGroupUsers = [i['userName'] for i in targetGroupJson['members']]

    srcGroupUsers = set(srcGroupUsers)
    targetGroupUsers = set(targetGroupUsers)

    missingUsers = srcGroupUsers - targetGroupUsers
    printLog("Missing users in group {} : ".format(group) , missingUsers)
    return missingUsers


def findAllArtifactsInPath(path,session):
    printLog("Finding all artifacts recursively in path: ", path)
    allArtifacts = []
    for root, dirs, files in os.walk(path):
        basePath = root.split(session+"/artifacts")[1]
        for file in files:
            allArtifacts.append(basePath + "/" + file)
    return allArtifacts

def findClashingNoteBookArtifacts(srcSession, targetSession):
    printLog("Finding clashing notebook artifacts")
    srcNotebookPath = srcSession + "/artifacts"
    targetNotebookPath = targetSession + "/artifacts"

    allSrcDir = os.listdir(srcNotebookPath)
    allTargetDir = os.listdir(targetNotebookPath)
    allClashingNotebooks = []
    for dir in allSrcDir:
        if os.path.isdir(srcNotebookPath + "/" + dir) and dir in allTargetDir:
            printLog('Directory: present in both source and target session: ', dir)
            srcNotebooks = findAllArtifactsInPath(srcNotebookPath + "/" + dir, srcSession)
            targetNotebooks = findAllArtifactsInPath(targetNotebookPath + "/" + dir, targetSession)
            clashingNotebooks = list(set(srcNotebooks) & set(targetNotebooks))
            printLog('Clashing notebooks: ', clashingNotebooks)
            print('Number of clashing notebooks in {}: '.format(dir), len(clashingNotebooks))
            allClashingNotebooks.extend(clashingNotebooks)

        elif not os.path.isdir(srcNotebookPath + "/" + dir) and dir in allTargetDir:
            printLog('File: present in both source and target session: ', dir)
            allClashingNotebooks.append(dir)
    return allClashingNotebooks



def getSourceJobLog(srcSession):
    printLog("Getting source job log for session: ", srcSession)
    srcJobLogPath = srcSession + "/jobs.log"

    allJobs = []
    with open(srcJobLogPath) as f:
        for line in f:
            job = json.loads(line)
            allJobs.append(job)
    return allJobs

def findClashingNotebooksWithJobs(srcSession,targetSession):
    allClashingNotebooks  = findClashingNoteBookArtifacts(srcSession, targetSession)
    srcJobs = getSourceJobLog(srcSession)

    notebookPathToJobId = {}

    for job in srcJobs:
        if 'notebook_task' in job['settings']:
            notebookPath = job['settings']['notebook_task']['notebook_path'] + '.dbc'
            if notebookPath not in notebookPathToJobId:
                notebookPathToJobId[notebookPath] = [job['job_id']]
            else:
                notebookPathToJobId[notebookPath].append(job['job_id'])
    clashingNotebooksWithJobs = []

    for notebook in allClashingNotebooks:
        if notebook in notebookPathToJobId:
            details = {}
            details['notebook'] = notebook
            details['job_ids'] = notebookPathToJobId[notebook]
            clashingNotebooksWithJobs.append(details)

    print()
    print()
    printLog('Clashing notebooks with jobs: ', clashingNotebooksWithJobs)
    print('Number of clashing notebooks with jobs: ', len(clashingNotebooksWithJobs))
    return clashingNotebooksWithJobs



if __name__ == '__main__':
    srcSession = 'incrm_notebook_oct_7_try_1' #input("Enter the source session: ")
    targetSession ='asiacrm_notebook_oct_7_try_1' #input("Enter the target session: ")

    if checkIfSessionExists(srcSession) == False:
        printLog("Source session does not exist")
        sys.exit()

    if checkIfSessionExists(targetSession) == False:
        printLog("Target session does not exist")
        sys.exit()

    # getUserGroupDiff(srcSession, targetSession)

    missingUsersInTarget = getAllUserDiff(srcSession, targetSession)
    print('Number of missing users in target session: ', len(missingUsersInTarget))

    clashingGroups = getUserGroupDiff(srcSession, targetSession)
    clashingGroups.remove('users')
    clashingGroups.remove('all_users')
    print('Number of clashing groups: ', len(clashingGroups))

    #finding missing users in common groups
    for group in clashingGroups:
        missingUsersInTargetGroup = findMissingUsersInGroup(srcSession, targetSession, group)
        if len(missingUsersInTargetGroup) > 0:
            print('Number of missing users in group {} : '.format(group), len(missingUsersInTargetGroup))


    print('---------------------')
    print()
    print()
    #clashingNotebooks = findClashingNoteBookArtifacts(srcSession, targetSession)
    #print('Number of clashing notebooks: ', len(clashingNotebooks))
    clashingNotebooksWithJobs = findClashingNotebooksWithJobs(srcSession, targetSession)
    for notebook in clashingNotebooksWithJobs:
        if len(notebook['job_ids'])>2:
            print('Notebook: ', notebook['notebook'],len(notebook['job_ids']))

    print()
    print()

