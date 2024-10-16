import os
import colorama
from time import time
from datetime import datetime as dt
from threading import Thread
import mysql.connector
import traceback
from config import db_config as dbConfig # this contains the database configuration

dbConfig['table'] = 'scrapping_report'

colorama.init()
RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
BLUE = colorama.Fore.BLUE
MAGENTA = colorama.Fore.MAGENTA
CYAN = colorama.Fore.CYAN
LIGHTYELLOW = colorama.Fore.LIGHTYELLOW_EX
LIGHTMAGENTA = colorama.Fore.LIGHTMAGENTA_EX
LIGHTCYAN = colorama.Fore.LIGHTCYAN_EX
RESET = colorama.Fore.RESET

width = 80

def getInBox(text, width = 20,color = None):
    text = str(text)
    l = len(text)
    spaces = (width-l)

    finalText = ''
    if spaces%2==0:
        finalText = ' '*(spaces//2) + text + ' '*(spaces//2)
    else:
        finalText = ' '*(spaces//2) + text + ' '*(spaces//2+1)

    if color:
        return f'{color}{finalText}{RESET}'
    else:
        return finalText    

def center_data(string):
        l = len(string)
        return ' '*((width-l)//2) + string

def stopWatch(start_time, track_string = "Time Elapsed"):
    global updated
    while not updated:
        currentTime = time()
        time_taken = currentTime-start_time
        time_taken = convertSeconds(time_taken)
        print(f'{LIGHTYELLOW}{track_string}: {time_taken}  ',end='\r')
        
    print(f'{LIGHTYELLOW}{track_string}: {time_taken}  ',end='\n')

def stopWatchControl(command, DisplayString = "Time Elapsed"):
    global updated
    command = command.lower()
    if 'start' in command:
        updated = False
        Thread(target=stopWatch, args=(time(),DisplayString)).start()
    elif 'stop' in command:
        updated = True

def convertSeconds(seconds):
    seconds = float(seconds)
    hours = int(seconds / 3600)
    seconds %= 3600
    minutes = int(seconds / 60)
    seconds %= 60

    time_str = f"[{hours}:{minutes}:{seconds:.2f}]"
    return time_str

def connectToSqlDb(host = dbConfig['host'],user = dbConfig['user'],password = dbConfig['passwd'],database = dbConfig['database']):
    
    try:
        connection = mysql.connector.connect(host=host,
                                            database=database,
                                            user=user,
                                            password=password)
        cursor = connection.cursor()
        return connection,cursor
    except Exception as e:
        raise Exception("DataBase Connection Error")
    
def getDataFromSql(cursor, query):
    try:
        cursor.execute(query)
        records = cursor.fetchall()
    except Exception as e:
        records = None
        print(f'{RED}Error: {e}')
    return records

def getHeadings(cursor, tableName):
    heads = [head[0] for head in getDataFromSql(cursor, f"describe {tableName}")]
    return heads

def disconnectFromSqlDb(connection,cursor):
    if connection.is_connected():
        cursor.close()
        connection.close()

def insertDataInDb(connection, cursor, data, tableName):
    try:
        heads = getHeadings(cursor, tableName)[1:]

        line = f'{LIGHTYELLOW}{"─"*width}'
        separation_line = f'{LIGHTYELLOW}{"─ "*(width//2)}'

        print(f'{GREEN}Data Insertion Started\n{RESET}')
        
        total = len(data)
        currentDate = dt.now().strftime("%Y-%m-%d %H:%M:%S")

        print(data)
        data = [row + [str(currentDate)]  for row in data]

        st = time()
        stopWatchControl('start', "Inserting in Database")
        sql_query = f"INSERT INTO {tableName} ({','.join(heads)}) VALUES ({','.join(['%s']*len(heads))})"

        cursor.executemany(sql_query, data)
        connection.commit()

        stopWatchControl('stop')
       
        et = time()
        insertionReport = '\n' + line + '\n'
        insertionReport += f'{MAGENTA}{center_data(f"Database Insertion Stats")}\n'
        insertionReport += separation_line + '\n'
        insertion_time = convertSeconds(et-st)
        time_per_entry = (et-st)/total
        insertionReport += f'{CYAN}{center_data(f"Total Time Taken: {insertion_time}")}\n'
        insertionReport += f'{BLUE}{center_data(f"Time Taken Per Entry: {time_per_entry:.3} seconds")}\n'
        insertionReport += line + '\n'
        print(insertionReport)
        
        return True
    except Exception as e:
        stopWatchControl('stop')
        print(f'{RED}\nError: {e}{RESET}')
        traceback.print_exc()
        return False

def getFinalDisplayString(statsData, currentFileName, brand, country):

    finalReportString = '\n' + getInBox(f'{"*"*20} REPORT {"*"*20}',21*4)+'\n'
    finalReportString += f'{getInBox(currentFileName,21*4)}\n'
    heads = f'|{getInBox("Category")} | {getInBox("Total Unique")} | {getInBox("Inserted")}|\n'
    lineWidth = len(heads) - 3

    finalReportString += ' ' + '-'*lineWidth + '\n'
    finalReportString += heads
    finalReportString += ' ' + '-'*lineWidth + '\n'
    
    for typ in statsData:
        typData = statsData[typ]
        if 'total_unique_products' not in typData:
            unique_prods = 'total_unique_poducts'
        else:
            unique_prods = 'total_unique_products'
        unique = typData[unique_prods]
        if 'pass' in typData:
            inserted_products = 'pass'
        else:
            inserted_products = "products_inserted"

        inserted = typData[inserted_products]
        
        if unique == 0:
            color = RED
        elif unique != inserted:
            color = YELLOW
        else:
            color = GREEN

        finalReportString += f'|{getInBox(typ,color = color)} | {getInBox(unique,color = color)} | {getInBox(inserted,color = color)}|\n'


    totalUnique = sum([statsData[typ][unique_prods] for typ in statsData])

    insertedProducts = sum([statsData[typ][inserted_products] for typ in statsData])
    failedProducts = totalUnique - insertedProducts

    finalReportString += ' ' + '-'*lineWidth + '\n'

    finalReportString += f'\nTotal Unique Products in {brand} {country}: {totalUnique}\n'
    finalReportString += f'Total Products inserted in DB: {insertedProducts}\n'
    finalReportString += f'Total Failed: {failedProducts}\n'

    return finalReportString

def makeDataFromDict(statsData, brand, country):
    
    current_month = dt.now().strftime('%B')
    current_year = dt.now().strftime('%Y')

    data = []
    for caretogy in statsData:
        typData = statsData[caretogy]
        if 'total_unique_products' not in typData:
            unique_prods = 'total_unique_poducts'
        else:
            unique_prods = 'total_unique_products'
        unique = typData[unique_prods]
        if 'pass' in typData:
            inserted = typData["pass"]
        else:
            inserted = typData["products_inserted"]
        url = typData["url"]
        
        row = [brand, country, current_month, current_year, caretogy, url, unique, inserted, '']
        data.append(row)
    return data

# if __name__ == "__main__":
#     statsData = {'Men Jeans': {'total_unique_products': 14, 'products_inserted': 1, 'url': 'https://www.patagonia.com/shop/mens-pants-jeans'}}
    
#     brand, country = 'PATAGONIA', "USA"
#     data = makeDataFromDict(statsData, brand, country)

#     connection,cursor = connectToSqlDb()
#     insertDataInDb(connection, cursor, data, dbConfig['table'])
#     disconnectFromSqlDb(connection,cursor)
#     print(RESET)

#     currentFileName = '53.patagonia_usa.py'

#     finalReportString = getFinalDisplayString(statsData, currentFileName, brand, country)
#     print(finalReportString)