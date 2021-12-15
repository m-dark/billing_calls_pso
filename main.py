#!/usr/bin/env python3.6

import os
import subprocess
import pymysql
import sys
import re
#sys.setdefaultencoding('utf-8')
from datetime import datetime

array_argv = []
outcid = set(['all'])

for param in sys.argv:
    array_argv.append(param)

result_date_start=re.match(r'([2][0]\d\d\.([0][1-9]|[1][0-2]).([0][1-9]|[1][0-9]|[2][0-9]|[3][0-1]))', array_argv[1])
if result_date_start is None:
    print('У даты начала не корректный формат (2022.01.01)!')
    sys.exit()
result_time_start=re.match(r'(\d\d\:\d\d:\d\d)', array_argv[2])
if result_time_start is None:
    print('Время начала имеет не корректный формат (00:00:00)!')
    sys.exit()
result_date_end=re.match(r'([2][0]\d\d\.([0][1-9]|[1][0-2]).([0][1-9]|[1][0-9]|[2][0-9]|[3][0-1]))', array_argv[3])
if result_date_end is None:
    print('У конечной даты не корректный формат (2039.01.31)!')
    sys.exit()
result_time_end=re.match(r'(\d\d\:\d\d:\d\d)', array_argv[4])
if result_time_end is None:
    print('Конечное время имеет не корректный формат (23:59:59)!')
    sys.exit()

asteriskdb = pymysql.connect(host="localhost", user="root", passwd="", db="asterisk", charset='utf8')
cursor_outcid = asteriskdb.cursor()
cursor_outcid.execute("SELECT outcid FROM trunks WHERE outcid != ''")
if cursor_outcid != '':
    for row_outcid in cursor_outcid:
        if row_outcid[0] not in outcid:
            outcid.add(row_outcid[0])
else:
    print('Error_01: На транках не настроены городские номера!')
cursor_outcid.close()
