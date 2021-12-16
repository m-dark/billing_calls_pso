#!/usr/bin/env python3.6
import os
import subprocess
import pymysql
import sys
import re
import logging
from datetime import datetime

date_time = datetime.strftime(datetime.now(), "%Y.%m.%d_%H-%M-%S")
dir_log = '/opt/asterisk/billing_calls_pso/log/'
log = logging.getLogger("billing_calls_pso")
fh = logging.FileHandler(dir_log+'billing_calls_pso.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] - %(name)s: %(message)s"))
log.addHandler(fh)
log.setLevel(logging.DEBUG)
log.info('Start "'+sys.argv[1]+' '+sys.argv[2]+' '+sys.argv[3]+' '+sys.argv[4]+'"')

array_argv = []
outcid_argv = set([])
outcid_db = set([])

def check_number(number):
    result_number=re.match(r'((all)|([3][4][3][23]\d{6})|([78][3][4][3][23]\d{6})|([23]\d{6}))$', number)
    if result_number is None:
        print('Не верный формат номера(ов)! '+number)
        log.error('Не верный формат номера(ов)! '+number)
        sys.exit()
    else:
        outcid_argv.add(number)

for param in sys.argv:
    array_argv.append(param)

result_date_start=re.match(r'([2][0]\d\d\.([0][1-9]|[1][0-2]).([0][1-9]|[1][0-9]|[2][0-9]|[3][0-1]))$', array_argv[1])
if result_date_start is None:
    print('У даты начала не корректный формат (2022.01.01)!')
    log.error('Не верный формат даты начала! '+array_argv[1])
    sys.exit()
result_time_start=re.match(r'(([01][0-9]|[2][0-3])\:([0-5][0-9])\:([0-5][0-9]))$', array_argv[2])
if result_time_start is None:
    print('Время начала имеет не корректный формат (00:00:00)!')
    log.error('Не верный формат времяни начала! '+array_argv[2])
    sys.exit()
result_date_end=re.match(r'([2][0]\d\d\.([0][1-9]|[1][0-2]).([0][1-9]|[1][0-9]|[2][0-9]|[3][0-1]))$', array_argv[3])
if result_date_end is None:
    print('У конечной даты не корректный формат (2039.01.31)!')
    log.error('Не верный формат даты у конечной даты! '+array_argv[3])
    sys.exit()
result_time_end=re.match(r'(([01][0-9]|[2][0-3])\:([0-5][0-9])\:([0-5][0-9]))$', array_argv[4])
if result_time_end is None:
    print('Конечное время имеет не корректный формат (23:59:59)!')
    log.error('Не верный формат времяни конца! '+array_argv[4])
    sys.exit()
result_znak=re.match(r'(\,)', array_argv[5])
if result_znak is None:
    array_numbers = array_argv[5].split(',')
    for number in array_numbers:
        check_number(number)
else:
    check_number(array_argv[5])

asteriskdb = pymysql.connect(host="localhost", user="root", passwd="", db="asterisk", charset='utf8')
cursor_outcid = asteriskdb.cursor()
cursor_outcid.execute("SELECT outcid FROM trunks WHERE outcid != ''")
if cursor_outcid != '':
    for row_outcid in cursor_outcid:
        if row_outcid[0] not in outcid_db:
            outcid_db.add(row_outcid[0])
else:
    print('Error_01: На транках не настроены городские номера!')
    log.error('Error_01: На транках не настроены городские номера!')
cursor_outcid.close()
asteriskdb.close()

asteriskcdrdb = pymysql.connect(host="localhost", user="root", passwd="", db="asteriskcdrdb", charset='utf8')
cursor = asteriskcdrdb.cursor()
file_calls=open(str(dir_log)+str(date_time)+'.csv', 'a')
for cid in outcid_argv:
    if cid == 'all':
        for number in outcid_db:
            cursor.execute("SELECT src,dst,billsec,calldate FROM cdr WHERE src = %s and (calldate between %s %s and %s %s) and lastdata != '' and billsec > '0' and disposition = 'ANSWERED' and dst > '0'", (number,array_argv[1],array_argv[2],array_argv[3],array_argv[4]))
            if cursor != '':
                for row_cursor in cursor:
                    if len(row_cursor[0]) == 7:
                        file_calls.write(row_cursor[0]+';'+row_cursor[1]+';'+str(row_cursor[2])+';'+str(row_cursor[3])+"\n")
                        continue
                    result_number=re.match(r'(343[23])', array_argv[0])
                    if result_number is None:
                        file_calls.write(row_cursor[0][3:10]+';'+row_cursor[1]+';'+str(row_cursor[2])+';'+str(row_cursor[3])+"\n")
                        continue
                    result_number=re.match(r'(7343[23])', array_argv[0])
                    if result_number is None:
                        file_calls.write(row_cursor[0][4:11]+';'+row_cursor[1]+';'+str(row_cursor[2])+';'+str(row_cursor[3])+"\n")
                        continue
                    result_number=re.match(r'(8343[23])', array_argv[0])
                    if result_number is None:
                        file_calls.write(row_cursor[0][4:11]+';'+row_cursor[1]+';'+str(row_cursor[2])+';'+str(row_cursor[3])+"\n")
                        continue
    else:
#        cursor.execute("SELECT src,dst,billsec,calldate FROM cdr WHERE src = %s and lastdata != '' and billsec > '0' and disposition = 'ANSWERED' and dst > '0'", (cid))
        cursor.execute("SELECT src,dst,billsec,calldate FROM cdr WHERE src = %s and (calldate between %s %s and %s %s) and lastdata != '' and billsec > '0' and disposition = 'ANSWERED' and dst > '0'", (cid,array_argv[1],array_argv[2],array_argv[3],array_argv[4]))
        if cursor != '':
            for row_cursor in cursor:
                if len(row_cursor[0]) == 7:
                    file_calls.write(row_cursor[0]+';'+row_cursor[1]+';'+str(row_cursor[2])+';'+str(row_cursor[3])+"\n")
                    continue
                result_number=re.match(r'(343[23])', array_argv[0])
                if result_number is None:
                    file_calls.write(row_cursor[0][3:10]+';'+row_cursor[1]+';'+str(row_cursor[2])+';'+str(row_cursor[3])+"\n")
                    continue
                result_number=re.match(r'(7343[23])', array_argv[0])
                if result_number is None:
                    file_calls.write(row_cursor[0][4:11]+';'+row_cursor[1]+';'+str(row_cursor[2])+';'+str(row_cursor[3])+"\n")
                    continue
                result_number=re.match(r'(8343[23])', array_argv[0])
                if result_number is None:
                    file_calls.write(row_cursor[0][4:11]+';'+row_cursor[1]+';'+str(row_cursor[2])+';'+str(row_cursor[3])+"\n")
                    continue
file_calls.close()
cursor.close()
asteriskcdrdb.close()
log.info('End "'+date_time+'.csv"')