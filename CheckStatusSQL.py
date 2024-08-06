import collections
from itertools import count
import sys
import pyodbc
import time
from asyncio.windows_events import NULL
from math import exp
from multiprocessing import connection
from sqlite3 import Cursor
import PySimpleGUI as sg
import ctypes
ctypes.windll.user32.ShowWindow( ctypes.windll.kernel32.GetConsoleWindow(), 0 )
from configparser import ConfigParser
from datetime import timedelta, date
from datetime import datetime
import datetime
import os
import schedule
from threading import Timer
from time import sleep
from collections import deque

count = 0
sg.theme('DarkGray2')
janelamenu = True
lista_log = deque('Verificao')


#LEITURA DO ARQUIVO#
config_object = ConfigParser()
config_object.read("config.ini")
userinfo = config_object["USERINFO"]
USER_SQL = (userinfo["login"])
PWD_SQL = (userinfo["password"])
Server_SQL = (userinfo["server"])
database = (userinfo["database"])


ultima_verificacao = datetime.datetime.now().second
verify = datetime.datetime.now().second

with open(f"log\log-{datetime.datetime.now().day}-{datetime.datetime.now().month}-HORA {datetime.datetime.now().hour}.txt", "a") as my_file:
    my_file.write(f'--Inicio o programa: {datetime.datetime.now()}\n')

driver_name = ''
driver_names = [x for x in pyodbc.drivers() if x.endswith(' for SQL Server')]
if driver_names:
    driver_name = driver_names[0]
if driver_name:
    conn_str = 'DRIVER={}; ...'.format(driver_name)

else:
    sg.Popup("Driver SQL nao encontrado na maquina")

def waitDb(Server_SQL, database, USER_SQL, PWD_SQL, maxAttempts, waitBetweenAttemptsSeconds,count):
    for attemptNumber in range(maxAttempts):
        cnxn = None
        try:
            cnxn = pyodbc.connect(f'DRIVER={{{driver_name}}};'
                                    'Server='+Server_SQL+';'
                                    'Database='+database+';'
                                    'UID=sa;'
                                    'ConnectRetryCount=2;'
                                    'PWD='+PWD_SQL+';'
                                    'autocommit=True')
            cursor = cnxn.cursor()
        except Exception as e:
            lista_log.clear()
            windowMenu['lista'].update(":...Tentando reconectar...:", text_color='red')
            windowMenu.refresh()
            lista_log.insert(1,f'*--ERRO--*Nao foi possivel conectar...: {datetime.datetime.now()}')
            with open(f"log\log-{datetime.datetime.now().day}-{datetime.datetime.now().month}-HORA {datetime.datetime.now().hour}.txt", "a") as my_file:
                my_file.write(f'*--ERRO--*Nao foi possivel conectar...: {datetime.datetime.now()}\n{e}\n')
        finally:
            if cnxn:
                lista_log.clear()
                lista_log.insert(1,f'Verificacao: {datetime.datetime.now()}')
                windowMenu['lista'].update(lista_log[0], text_color='green')
                cursor.execute("SELECT @@version;") 
                row = cursor.fetchone() 
                while row: 
                    row = cursor.fetchone()
                try:
                    cursor.close()
                    print(row)
                    if row == None:
                        print(count)
                        if count == 2000:
                            with open(f"log\log-{datetime.datetime.now().day}-{datetime.datetime.now().month}-HORA {datetime.datetime.now().hour}.txt", "a") as my_file:
                                my_file.write(f'*--CONECTADO*-- {datetime.datetime.now()}\n')
                            
                    else:
                        print('fora')
                    cursor.close()
                except Exception as printado:
                    print(printado)
                #with open(f"log\log-{datetime.datetime.now().day}-{datetime.datetime.now().month}-HORA {datetime.datetime.now().hour}.txt", "a") as my_file:
                #    my_file.write(f'--Reconectou ao BD: {datetime.datetime.now()}\n')

                ultima_verificacao = datetime.datetime.now().second
                return True
            else:
                #sg.Popup("DB no running yet on attempt numer " + str(attemptNumber))
                lista_log.clear()
                windowMenu['lista'].update(lista_log, text_color='red')
                lista_log.insert(1,f'(DB no running yet on attempt numer - {str(attemptNumber)} - {datetime.datetime.now()}')
                with open(f"log\log-{datetime.datetime.now().day}-{datetime.datetime.now().month}-HORA {datetime.datetime.now().hour}.txt", "a") as my_file:
                    my_file.write(f'*--Tentativas de reconexao - N: {str(attemptNumber)} - {datetime.datetime.now()}\n')

            time.sleep(waitBetweenAttemptsSeconds)
    lista_log.clear()
    windowMenu['lista'].update(lista_log, text_color='red')
    lista_log.insert(1,f'Max attempts waiting for DB to come online exceeded - {str(attemptNumber)} - {datetime.datetime.now()}')
    with open(f"log\log-{datetime.datetime.now().day}-{datetime.datetime.now().month}-HORA {datetime.datetime.now().hour}.txt", "a") as my_file:
        my_file.write(f'Maximo de tentativas excedidas | {str(attemptNumber)} - {datetime.datetime.now()}\n')
    #sg.Popup("Max attempts waiting for DB to come online exceeded")
    
    

while janelamenu:

    verifica_pasta = os.path.exists('log')
    if verifica_pasta == False:
        os.mkdir('log')

    #LAYOUT MENU 1#
    layout = [
    [sg.Text('======================================\n                        Check Status - SQL         \n======================================')],
    [sg.Button("Testar"),sg.Button("Configuracoes"),sg.Button("Sair")],
    [sg.Text("Tempo:"),sg.Text('00:00:00', key='tempo')],
    [sg.Text("Versao: 310124")],
    ]

    #LAYOUT MENU 1#
    layout_2 = [
    [sg.Text("Ultimas verificaoes", key='lista', text_color='green')],
    ]
    layout_frame =[
    [sg.Frame("", layout,element_justification='c')]
    ]
    layout_frame2 =[
        [sg.Frame("", layout_2,element_justification='c')]
        ]

    #LAYOUT CONFIG#
    layout_config = [
     [sg.Text('Usuario SQL: '), sg.InputText(''+USER_SQL)],
     [sg.Text('Senha SQL: '), sg.InputText(''+PWD_SQL)],
     [sg.Text('Server SQL: '), sg.InputText(''+Server_SQL)],  
     [sg.Text('Banco de dados: '), sg.InputText(''+database)],  
     [sg.Button('Salvar'), sg.Button('Cancelar')]
    ]

    layout_menu = [
        [sg.Frame("Menu",layout_frame, element_justification='c'),
        sg.Frame("Monitor",layout_frame2, element_justification='c')]]

    windowMenu = sg.Window('Check Status - SQL', layout_menu, finalize=True, disable_close=True)
    windowConf = sg.Window('Configuracoes', layout_config, finalize=True, disable_close=True,element_justification='c')
    windowConf.Hide()
    event, values = windowMenu.read()

    if event == sg.WINDOW_CLOSED or event == "Testar":
        minute = None
        while True:

            waitDb(Server_SQL, database, USER_SQL, PWD_SQL, 4, 5,count)
            count = (count + 1)
            if count == 2050:
                count = 0
            event, values = windowMenu.read(timeout=2)

            windowMenu['lista'].update(lista_log)

            if event == 'Sair': 
                paused = True
                janelamenu = False
                break
                windowConf.Close()
                windowMenu.Close()
                    
    if event == sg.WINDOW_CLOSED or event == "Configuracoes":
        windowMenu.Hide()
        windowConf.UnHide()
        event, values = windowConf.read()
        USER_SQL = (values[0])
        PWD_SQL = (values[1])
        Server_SQL = (values[2])
        database = (values[3])

        if event == sg.WINDOW_CLOSED:
            janelamenu = False
            break

        if event == 'Salvar':
            windowConf.Hide()
            windowMenu.UnHide()
            event, values = windowMenu.read()

            config_object = ConfigParser()
            config_object.read("config.ini")

            userinfo = config_object["USERINFO"]

            userinfo["password"] = PWD_SQL
            userinfo["login"] = USER_SQL
            userinfo["server"] = Server_SQL
            userinfo["database"] = database

            with open('config.ini', 'w') as conf:
                config_object.write(conf)

    if event == 'Sair': 
        janelamenu = False
        break
        windowConf.Close()
        windowMenu.Close()

    if event == sg.WINDOW_CLOSED: 
        janelamenu = False
        break
        windowConf.Close()
        windowMenu.Close()

    windowConf.Close()
    windowMenu.Close()
