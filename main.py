#!/usr/bin/env python3.6

import os
import subprocess
import pymysql
import sys
import re
import logging
#sys.setdefaultencoding('utf-8')
from datetime import datetime

date_time = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
dir_log = '/opt/asterisk/billing_calls_pso/log/'
log = logging.getLogger("billing_calls_pso")
fh = logging.FileHandler(dir_log+'billing_calls_pso.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] - %(name)s: %(message)s"))
log.addHandler(fh)
log.setLevel(logging.DEBUG)
log.info('Start')

array_argv = []
outcid = set(['all'])

def check_number(number):
    result_number=re.match(r'(([3][4][3][23]\d{6})|([78][3][4][3][23]\d{6})|([23]\d{6}))$', number)
    if result_number is None:
        print('Не верный формат номера(ов)! '+number)
        log.error('Не верный формат номера(ов)! '+number)
        sys.exit()

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
        if row_outcid[0] not in outcid:
            outcid.add(row_outcid[0])
else:
    print('Error_01: На транках не настроены городские номера!')
    log.error('Error_01: На транках не настроены городские номера!')
cursor_outcid.close()

log.info('End')

