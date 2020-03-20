'''
@Author: your name
@Date: 2020-03-17 10:26:01
@LastEditTime: 2020-03-17 10:39:40
@LastEditors: Please set LastEditors
@Description: In User Settings Edita
@FilePath: \data process\loger.py
'''
import json

class logger():
    def __init__(self,log_path):
        ''' log path'''
        self.path=log_path

    def _write_json(self,filename,data,mode='w+'):
        file_path='{}/{}'.format(self.path,filename)       
        with open(file_path,mode) as f:
            json.dump(data,f)
            print('Logging json completed')
    def Log_append(self,filename,data):
        self._write_json(filename,data,'a')

    def Log_write(self,filename,data):
        self._write_json(filename,data)
    