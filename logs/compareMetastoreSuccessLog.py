import json


def getAllTablesFromSuccessLog(session):
    logPath = session + '/success_metastore.log'
    allTables = []
    with open(logPath) as f:
        for line in f:
            tableDetails = json.loads(line)
            if 'source_zero' in tableDetails['table'] or 'source_delta' in tableDetails['table']:
                continue
            allTables.append(tableDetails['table'])
    return allTables

def getClashingTablesDbWise(srcSession,targetSession):
    srcTables = getAllTablesFromSuccessLog(srcSession)
    targetTables = getAllTablesFromSuccessLog(targetSession)

    clashingTables = {}

    for table in srcTables:
        if table in targetTables:
            db = table.split('.')[0]
            if db not in clashingTables:
                clashingTables[db] = [table]
            else:
                clashingTables[db].append(table)
    return clashingTables


if __name__ == '__main__':
    print("starting metastore compare")
    srcSession = 'incrm_notebook_oct_16_metastore_try2' #input("Enter the source session: ")
    targetSession ='asiacrm_notebook_oct_16_metastore_try1' #input("Enter the target session: ")
    clashingTables = getClashingTablesDbWise(srcSession,targetSession)
    sum = 0
    for db in clashingTables:
        print()
        print("clashing tables in db: ", db)
        print(clashingTables[db])
        sum += len(clashingTables[db])

    print("total clashing tables: ", sum)
    print("number of dbs with clashing tables: ", len(clashingTables))

    #dump clash tables to csv
    with open('clashingTables.csv', 'w') as f:
        f.write('db,table\n')
        for db in clashingTables:
            for table in clashingTables[db]:
                f.write(db + ',' + table.split('.')[1] + '\n')

