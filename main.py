#!/usr/bin/env python3.6
import os
import subprocess
import pymysql
import sys
import re
import logging
import configemail
from datetime import datetime
import smtplib
# Добавляем необходимые подклассы - MIME-типы
import mimetypes                                            # Импорт класса для обработки неизвестных MIME-типов, базирующихся на расширении файла
from email import encoders                                  # Импортируем энкодер
from email.mime.base import MIMEBase                        # Общий тип
from email.mime.text import MIMEText                        # Текст/HTML
from email.mime.image import MIMEImage                      # Изображения
from email.mime.audio import MIMEAudio                      # Аудио
from email.mime.multipart import MIMEMultipart              # Многокомпонентный объект

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

def send_email(addr_to, msg_subj, msg_text, files):
    addr_from = configemail.hostname.nodename               # Отправитель
##    password  = "password"                                  # Пароль
    msg = MIMEMultipart()                                   # Создаем сообщение
    msg['From']    = addr_from                              # Адресат
    msg['To']      = addr_to                                # Получатель
    msg['Subject'] = msg_subj                               # Тема сообщения
    body = msg_text                                         # Текст сообщения
    msg.attach(MIMEText(body, 'plain'))                     # Добавляем в сообщение текст
    process_attachement(msg, files)

    #======== Этот блок настраивается для каждого почтового провайдера отдельно ===============================================
##    server = smtplib.SMTP_SSL('127.0.0.1', 465)           # Создаем объект SMTP
    #server.starttls()                                      # Начинаем шифрованный обмен по TLS
    #server.set_debuglevel(True)                            # Включаем режим отладки, если не нужен - можно закомментировать
##    server.login(addr_from, password)                     # Получаем доступ
    server = smtplib.SMTP('localhost')
    server.set_debuglevel(0)
    server.send_message(msg)                                # Отправляем сообщение
    server.quit()                                           # Выходим
    #==========================================================================================================================

def process_attachement(msg, files):                        # Функция по обработке списка, добавляемых к сообщению файлов
    for f in files:
        if os.path.isfile(f):                               # Если файл существует
            attach_file(msg,f)                              # Добавляем файл к сообщению
        elif os.path.exists(f):                             # Если путь не файл и существует, значит - папка
            dir = os.listdir(f)                             # Получаем список файлов в папке
            for file in dir:                                # Перебираем все файлы и...
                attach_file(msg,f+"/"+file)                 # ...добавляем каждый файл к сообщению

def attach_file(msg, filepath):                             # Функция по добавлению конкретного файла к сообщению
    filename = os.path.basename(filepath)                   # Получаем только имя файла
    ctype, encoding = mimetypes.guess_type(filepath)        # Определяем тип файла на основе его расширения
    if ctype is None or encoding is not None:               # Если тип файла не определяется
        ctype = 'application/octet-stream'                  # Будем использовать общий тип
    maintype, subtype = ctype.split('/', 1)                 # Получаем тип и подтип
    if maintype == 'text':                                  # Если текстовый файл
        with open(filepath) as fp:                          # Открываем файл для чтения
            file = MIMEText(fp.read(), _subtype=subtype)    # Используем тип MIMEText
            fp.close()                                      # После использования файл обязательно нужно закрыть
    elif maintype == 'image':                               # Если изображение
        with open(filepath, 'rb') as fp:
            file = MIMEImage(fp.read(), _subtype=subtype)
            fp.close()
    elif maintype == 'audio':                               # Если аудио
        with open(filepath, 'rb') as fp:
            file = MIMEAudio(fp.read(), _subtype=subtype)
            fp.close()
    else:                                                   # Неизвестный тип файла
        with open(filepath, 'rb') as fp:
            file = MIMEBase(maintype, subtype)              # Используем общий MIME-тип
            file.set_payload(fp.read())                     # Добавляем содержимое общего типа (полезную нагрузку)
            fp.close()
            encoders.encode_base64(file)                    # Содержимое должно кодироваться как Base64
    file.add_header('Content-Disposition', 'attachment', filename=filename) # Добавляем заголовки
    msg.attach(file)                                        # Присоединяем файл к сообщению

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
                    number_b = str(row_cursor[1])
                    result_number=re.match(r'([23]\d{6})$', row_cursor[1])
                    if result_number is not None:
                        number_b='8343'+str(row_cursor[1])
                    if len(row_cursor[0]) == 7:
                        file_calls.write(row_cursor[0]+';'+number_b+';'+str(row_cursor[2])+';'+str(row_cursor[3])+',001;'+"\n")
                        continue
                    result_number=re.match(r'(343[23]\d{6})$', row_cursor[0])
                    if result_number is not None:
                        file_calls.write(row_cursor[0][3:10]+';'+number_b+';'+str(row_cursor[2])+';'+str(row_cursor[3])+',001;'+"\n")
                        continue
                    result_number=re.match(r'(7343[23]\d{6})$', row_cursor[0])
                    if result_number is not None:
                        file_calls.write(row_cursor[0][4:11]+';'+number_b+';'+str(row_cursor[2])+';'+str(row_cursor[3])+',001;'+"\n")
                        continue
                    result_number=re.match(r'(8343[23]\d{6})$', row_cursor[0])
                    if result_number is not None:
                        file_calls.write(row_cursor[0][4:11]+';'+number_b+';'+str(row_cursor[2])+';'+str(row_cursor[3])+',001;'+"\n")
                        continue
    else:
#        cursor.execute("SELECT src,dst,billsec,calldate FROM cdr WHERE src = %s and lastdata != '' and billsec > '0' and disposition = 'ANSWERED' and dst > '0'", (cid))
        cursor.execute("SELECT src,dst,billsec,calldate FROM cdr WHERE src = %s and (calldate between %s %s and %s %s) and lastdata != '' and billsec > '0' and disposition = 'ANSWERED' and dst > '0'", (cid,array_argv[1],array_argv[2],array_argv[3],array_argv[4]))
        if cursor != '':
            for row_cursor in cursor:
                number_b = str(row_cursor[1])
                result_number=re.match(r'([23]\d{6})$', row_cursor[1])
                if result_number is not None:
                    number_b ='8343'+str(row_cursor[1])
                if len(row_cursor[0]) == 7:
                    file_calls.write(row_cursor[0]+';'+number_b+';'+str(row_cursor[2])+';'+str(row_cursor[3])+',001;'+"\n")
                    continue
                result_number=re.match(r'(343[23]\d{6})$', row_cursor[0])
                if result_number is not None:
                    file_calls.write(row_cursor[0][3:10]+';'+number_b+';'+str(row_cursor[2])+';'+str(row_cursor[3])+',001;'+"\n")
                    continue
                result_number=re.match(r'(7343[23]\d{6})$', row_cursor[0])
                if result_number is not None:
                    file_calls.write(row_cursor[0][4:11]+';'+number_b+';'+str(row_cursor[2])+';'+str(row_cursor[3])+',001;'+"\n")
                    continue
                result_number=re.match(r'(8343[23]\d{6})$', row_cursor[0])
                if result_number is not None:
                    file_calls.write(row_cursor[0][4:11]+';'+number_b+';'+str(row_cursor[2])+';'+str(row_cursor[3])+',001;'+"\n")
                    continue
file_calls.close()
cursor.close()
asteriskcdrdb.close()

# Использование функции send_email()
addr_to = configemail.email_to                                      # Получатель
files = [dir_log+date_time+'.csv']                                  # Список файлов, если вложений нет, то files=[]

numbers = array_argv[5]
if array_argv[5] == 'all':
    numbers = outcid_db

send_email(addr_to, 'Отчет по звонкам', 'Информация о звонках'+"\n"+'С:  '+str(array_argv[1])+' '+str(array_argv[2])+"\n"+'До: '+str(array_argv[3])+' '+str(array_argv[4])+''+"\n"+'По номерам: '+str(outcid_db)+"\n", files)

log.info('End "'+date_time+'.csv"')