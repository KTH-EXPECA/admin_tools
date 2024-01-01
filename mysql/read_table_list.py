import mysql.connector
import json
import mysqlmod as m
import os
import sys


os.chdir(sys.path[0])            # Set current directory to script directory


def main():

    dbname = 'dummy_db'

    with open('config.json', 'r') as f:
        config = json.load(f)

    config['database'] = dbname

    with mysql.connector.connect(**config) as connection:          
        table_list = m.read_table_list(connection)
        for table in table_list:
            print(table)
    
    return


if __name__ == "__main__":
    main()







