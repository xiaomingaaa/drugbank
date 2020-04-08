'''
@Author: ma tengfei
@Date: 2020-03-09 16:55:41
@LastEditTime: 2020-04-08 15:59:28
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: /KG/data/mesh.py
'''
from bs4 import BeautifulSoup
import random
import ssl
from urllib import request
import urllib
import re
from http_utils import HttpGet
header = {'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip, deflate, br',
          'Connection': 'keep-alive', 'Accept-Language': 'zh-CN,zh;q=0.9'}


def mesh_casnum():
    mesh_exist = set()
    with open('mesh_drugbank.tsv', 'r') as f:
        for line in f:
            mesh = line.strip().split('\t')[0]
            mesh_exist.add(mesh)
    file = open('mesh_drugbank.tsv', 'a')
    with open('data/chemical_meshid.tsv', 'r') as f:
        for idx, line in enumerate(f):
            if idx == 0:
                continue
            name, dd = line.strip().split('\t')[:2]
            if dd.strip() in mesh_exist:
                continue
            meshid = dd.strip().split(':')[2]

            url = 'https://meshb.nlm.nih.gov/api/search/record?searchInField=ui&sort=&size=20&searchType=exactMatch&searchMethod=FullWord&q={}'.format(
                meshid)

            data = HttpGet(url, header)

            first = data['hits']['hits']
            if len(first) > 0:
                second = first[0]['_source']['ConceptList']['Concept'][0]
                registry_num = second['RegistryNumber']
                try:
                    casnum = registry_num['t']
                except Exception as e:
                    casnum = registry_num
                file.write(dd+'\t'+casnum+'\n')
                print(casnum)

ssl._create_default_https_context = ssl._create_unverified_context
proxy_list = [
    {"http": "124.88.67.54:80"},
    {"http": "61.135.217.7:80"},
    {"http": "42.231.165.132:8118"},
    {'http': '13.229.121.73:3128'},
    {'http': '202.85.213.219:3128'},
    {'http': '98.191.98.146:3128'},
    {'http': '188.166.220.104:443'},
    {'http': '128.199.190.243:443'},
    {'http': '222.124.22.133:8080'},
    {'http': '128.199.138.78:443'},
    {'http': '118.114.77.47:8080'},
    {'http': '122.72.108.53:80'},
    {'http': '185.21.77.83:3128'},
    {'http': '191.222.194.90:8080'},
    {'http': '177.6.147.202:8080'},
]
proxy = random.choice(proxy_list)
log = open('log_drugbank1.txt', 'w')


def getContent(url):

    try:
        proxy = random.choice(proxy_list)  # 使用代理查询库
        httpproxy_handler = request.ProxyHandler(proxy)
        opener = request.build_opener(httpproxy_handler)
        data = request.urlopen(url, timeout=10).read().decode('utf-8')
    except Exception as e:
        print('error: '+url)
        log.write(url+'\n')
        return []

    soup = BeautifulSoup(data, 'html.parser')
    contents = []
    temp1 = soup.findAll('a')
    for k in temp1:
        if 'http://fdasis.nlm.nih.gov/srs/srsdirect.jsp?regno' in k['href']:
            contents.append(k.string)
    temp = soup.findAll('dd', class_='col-md-10 col-sm-8')
    for k in temp:
        if not k.string:
            continue
        drug_re = re.compile(r'([0-9]{1,}-[0-9]+-[0-9]+)')

        d = drug_re.search(k.string)
        if d:
            contents.append(k.string)

    return contents


def process_error():
    file = open('drugbank_cas.txt', 'w')
    with open('log_drugbank.txt', 'r') as f:
        for line in f:
            d = line.strip()[-7:]
            print(d)
            contents = getContent(line.strip())
            for i in contents:
                file.write(d+'\t'+i+'\n')


def get_drugs_info(filename):
    import pandas as pd
    db = dict()

    df = pd.read_csv(filename)
    data = df.to_dict(orient='records')
    for d in data:
        temp = dict()
        temp['name'] = d['name']
        temp['type'] = d['type']
        temp['description'] = d['description']
        temp['indication'] = d['indication']
        temp['groups'] = d['groups']
        temp['smiles'] = d['smiles']
        temp['cas-num'] = d['cas-num']
        temp['unii'] = d['unii']
        db[d['drugbank_id'].strip()] = temp
    return db


def mesh_to_drugbank():
    import pandas as pd
    db = get_drugs_info('data/drugs_info.csv')
    mesh_ids = dict()
    with open('mesh_drugbank.tsv', 'r') as f:
        for line in f:
            mesh, id = line.strip().split('\t')
            if id == '0':
                continue
            mesh_ids[id] = mesh
    maps = list()
    for drugid in db:
        cas_num = db[drugid]['cas-num']
        unii = db[drugid]['unii']
        temp = dict()
        if cas_num in mesh_ids:
            temp['mesh id'] = mesh_ids[cas_num]
            temp['drugbank id'] = drugid
            maps.append(temp)
            continue
        if unii in mesh_ids:
            temp['mesh id'] = mesh_ids[unii]
            temp['drugbank id'] = drugid
            maps.append(temp)

    data = pd.DataFrame(maps)
    data.to_csv('mesh_drugank.tsv', sep='\t', index=False)


if __name__ == "__main__":
    #提取mesh数据库中cas_num
    mesh_casnum()
    mesh_to_drugbank()
