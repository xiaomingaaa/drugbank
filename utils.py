'''
@Author: your name
@Date: 2020-03-17 10:53:55
LastEditTime: 2021-06-22 14:29:45
LastEditors: Please set LastEditors
@Description: common toolkit include logger, debugger
'''
import json
import sys
import urllib
from urllib import request
import ssl
import random
import requests
import pandas as pd

ssl._create_default_https_context=ssl._create_unverified_context
proxy_list = [
{"http":"124.88.67.54:80"},
{"http":"61.135.217.7:80"},
{"http":"42.231.165.132:8118"},
{'http':'13.229.121.73:3128'},
{'http':'202.85.213.219:3128'},
{'http':'98.191.98.146:3128'},
{'http':'188.166.220.104:443'},
{'http':'128.199.190.243:443'},
{'http':'222.124.22.133:8080'},
{'http':'128.199.138.78:443'},
{'http':'118.114.77.47:8080'},
{'http':'122.72.108.53:80'},
{'http':'185.21.77.83:3128'},
{'http':'191.222.194.90:8080'},
{'http':'177.6.147.202:8080'},
]

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

def catch_error():
    def inner1(f):
        def inner2(*args,**kwargs):
            try:
                res=f(*args,**kwargs)
            except Exception as e:
                info=sys.exc_info()[2].tb_frame.f_back
                temp = "filename:{}\nlines:{}\tfuncation:{}\terror:{}"
                temp.format(info.f_code.co_filename, info.f_lineno, f.__name__, repr(err))

def get_data_by_url(url):

    proxy=random.choice(proxy_list)
    httpproxy_handler = request.ProxyHandler(proxy)
    opener = request.build_opener(httpproxy_handler)
    data=request.urlopen(url,timeout=10).read().decode('utf-8') 
    return data     

def get_drug4atc(filepath):
    data=pd.read_csv(filepath,header=0)
    ### drop缺失值
    data=pd.DataFrame(data,columns=['drugbank_id','name','atc_codes']).dropna(axis=0, how='any', thresh=None, subset=None, inplace=False)
    data.to_csv('drug4atc.tsv',sep='\t',index=False)

if __name__=='__main__':
    get_drug4atc('BioDb/drugbank/drugs_info_5_1_8.csv')

        