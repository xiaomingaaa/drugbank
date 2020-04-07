'''
@Author: Ma Tengfei
@Date: 2020-03-16 21:33:33
@LastEditTime: 2020-04-07 10:34:12
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: \data process\httputil.py
'''
import sys
import re
import pandas as pd
from bs4 import BeautifulSoup

from utils import logger, get_data_by_url

'''
@description: get drug sdf data from drugbank
@param {type} sdf_path: store path
@return: 
'''
def SaveSDF(drugid, sdf_path, log: logger):
    file_path = '{}/{}.sdf'.format(sdf_path, drugid)
    try:
        url = 'https://www.drugbank.ca/structures/small_molecule_drugs/'+drugid+'.sdf'
        data = get_data_by_url(url)
    except Exception as e:
        info = sys.exc_info()[2].tb_frame.f_back
        temp = dict()
        temp['type'] = 'sdf process'
        temp['drug_id'] = drugid
        temp['info'] = 'file: {}, lines: {}, error: {}'.format(
            info.f_code.co_filename, info.f_lineno, repr(e))
        temp['url'] = url
        log.Log_append('log_sdf_drugbank.json', temp)
        return
    with open(file_path, 'wt', encoding='utf-8') as f:
        f.write(data)


'''
@description: 从drugbank上获取drug相关信息
@param {type} drug_list,待获取的药物的列表
@return: 
'''
def SaveDrugInfo(drug_list, save_path, filename, log: logger, file_type='excel'):
    file_path = '{}/{}'.format(save_path, filename)
    drugs_info = list()
    for drugid in drug_list:
        try:
            url = 'https://www.drugbank.ca/drugs/{}'.format(drugid)
            data = get_data_by_url(url)
        except Exception as e:
            info = sys.exc_info()[2].tb_frame.f_back
            temp = dict()
            temp['type'] = 'drug info process'
            temp['drug_id'] = drugid
            temp['info'] = 'file: {}, lines: {}, error: {}'.format(
                info.f_code.co_filename, info.f_lineno, repr(e))
            temp['url'] = url
            log.Log_append('log_druginfo_drugbank.json', temp)
        soup = BeautifulSoup(data, 'html.parser')
        # find smiles <div>
        smiles = soup.find_all('div', class_='wrap')
        # find cas number <dd>
        info = soup.find_all('dd', class_='col-md-10 col-sm-8')
        info_temp = dict()
        info_temp['drug_id'] = drugid
        if len(smiles) > 0:
            info_temp['smiles'] = smiles[-1].getText()
        if info:
            weight_re = re.compile(r'[^\.\d](\d+\.\d+|\d+)[^\.\d]')
            cas_re = re.compile(r'([0-9]{1,}-[0-9]+-[0-9]+)')
            if info[0]:
                info_temp['drug_name'] = info[0].string
            if info[2]:
                info_temp['drug_type'] = info[2].string
            for k in info:
                if len(k.contents) > 0:
                    if 'Average' in k.contents[0]:
                        weight = weight_re.findall(k.contents[0])
                        if len(weight) > 0:
                            info_temp['matter'] = weight[0]
                if not k.string:
                    continue
                cas_num = cas_re.findall(k.string)
                if len(cas_num) == 1:
                    info_temp['cas_number'] = cas_num[0]
        drugs_info.append(info_temp)
    df = pd.DataFrame(drugs_info)
    if file_type == 'excel':
        df.to_excel(file_path)
    elif file_type == 'csv':
        df.to_csv(file_path)


'''
@description: 从uniprot数据库中获取对应数据库的id映射
@param {type} tran的选值可参考连接：https://www.uniprot.org/help/api_idmapping
@return: 
'''
def UniprotToOtherDB(uniprot_list, savepath, filename, tran='P_ENTREZGENEID', savetype='csv'):
    file_path = '{}/{}'.format(savepath, filename)
    # uniprot api
    url = 'https://www.uniprot.org/uploadlists/'

    if isinstance(uniprot_list, list):
        param = ''
        for i in uniprot_list:
            param += ' '+i
        params = {
            'from': 'ACC+ID',
            'to': tran,
            'format': 'tab',
            'query': param
        }
    elif isinstance(uniprot_list, dict):
        param = ''
        for i in list(uniprot_list.keys()):
            param += ' '+i
        params = {
            'from': 'ACC+ID',
            'to': tran,
            'format': 'tab',
            'query': param
        }
    else:
        print('** data type is not supported **')
        return
    import urllib
    data = urllib.parse.urlencode(params)
    data = data.encode('utf-8')
    req = urllib.request.Request(url, data)
    pairs = list()
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            response = f.read()
        content = response.decode('utf-8')
        tt = content.strip().split('\n')
        if len(tt) > 1:
            for i in tt[1:-1]:
                info_temp = dict()
                protein, target_value = i.strip().split('\t')[:2]
                info_temp['uniprot_id'] = protein
                info_temp[tran] = target_value
                pairs.append(info_temp)
        df = pd.DataFrame(pairs)
        if savetype == 'csv':
            df.to_csv(file_path)
        elif savetype == 'excel':
            df.to_excel(file_path)
        elif savetype == 'tsv':
            df.to_csv(file_path, sep='\t')
        else:
            print('** data type is not supported **')
        # if len(tt)>1:
        #     return tt[1].strip().split('\t')[1]
    except Exception as e:
        print(e)

'''
从drugbank的xml数据文件中读取drug信息
'''
def parse_drugs_drugbank(xmlfile, savepath, filename, savetype='excel'):
    import xml.etree.ElementTree as ET
    import collections
    import json
    save_file = '{}/{}'.format(savepath, filename)
    tail = xmlfile[-3:]
    print(f'process file: {xmlfile}')
    if tail == 'zip':
        import zipfile
        with zipfile.ZipFile(xmlfile) as zipfile:
            f = zipfile.open(xmlfile.split('/')[-1].strip('.zip'))
            tree = ET.parse(f)
            f.close()
    elif '.gz'==tail:
        import gzip
        with gzip.open(xmlfile) as f:
            tree=ET.parse(f)
    else:
        with open(xmlfile) as f:
            tree = ET.parse(f)
    print('read complete!')
    root = tree.getroot()
    ns = '{http://www.drugbank.ca}'
    inchikey_template = "{ns}calculated-properties/{ns}property[{ns}kind='InChIKey']/{ns}value"
    inchi_template = "{ns}calculated-properties/{ns}property[{ns}kind='InChI']/{ns}value"
    smiles_template = "{ns}calculated-properties/{ns}property[{ns}kind='SMILES']/{ns}value"
    rows = list()
    for i, drug in enumerate(root):
        row = collections.OrderedDict()
        assert drug.tag == ns + 'drug'
        row['type'] = drug.get('type')
        row['drugbank_id'] = drug.findtext(ns + "drugbank-id[@primary='true']")
        row['name'] = drug.findtext(ns + "name")
        row['description'] = drug.findtext(ns + "description")
        row['indication'] = drug.findtext(ns+"indication")
        row['unii'] = drug.findtext(ns+'unii')
        row['cas-num'] = drug.findtext(ns+'cas-number')
        row['groups'] = [group.text for group in
                         drug.findall("{ns}groups/{ns}group".format(ns=ns))]
        row['atc_codes'] = [code.get('code') for code in
                            drug.findall("{ns}atc-codes/{ns}atc-code".format(ns=ns))]
        row['categories'] = [x.findtext(ns + 'category') for x in
                             drug.findall("{ns}categories/{ns}category".format(ns=ns))]
        row['inchi'] = drug.findtext(inchi_template.format(ns=ns))
        row['inchikey'] = drug.findtext(inchikey_template.format(ns=ns))
        row['smiles'] = drug.findtext(smiles_template.format(ns=ns))
        # Add drug aliases
        aliases = {
            elem.text for elem in
            drug.findall("{ns}international-brands/{ns}international-brand".format(ns=ns)) +
            drug.findall("{ns}synonyms/{ns}synonym[@language='English']".format(ns=ns)) +
            drug.findall("{ns}international-brands/{ns}international-brand".format(ns=ns)) +
            drug.findall("{ns}products/{ns}product/{ns}name".format(ns=ns))

        }
        aliases.add(row['name'])
        row['aliases'] = sorted(aliases)

        rows.append(row)

    # 将aliases写入json文件
    alias_dict = {row['drugbank_id']: row['aliases'] for row in rows}
    with open(f'{savepath}/aliases.json', 'w') as fp:
        json.dump(alias_dict, fp, indent=2, sort_keys=True)

    def collapse_list_values(row):
        for key, value in row.items():
            if isinstance(value, list):
                row[key] = '|'.join(value)
        return row
    rows = list(map(collapse_list_values, rows))
    df = pd.DataFrame(rows)
    if savetype == 'excel':
        df.to_excel(save_file, index=False)
    elif savetype == 'csv':
        df.to_csv(save_file, index=False)
    else:
        print('** Data type is not supported! **')

    print('all drugs processed!')
    print('filter approved small molecule!')

    drugbank_sm = df[
        df.groups.map(lambda x: 'approved' in x) &
        df.inchi.map(lambda x: x is not None) &
        df.type.map(lambda x: x == 'small molecule')
    ]
    if savetype == 'excel':
        drugbank_sm.to_excel(
            savepath+'/drugbank_small_molecule.xlsx', index=False)
    elif savetype == 'csv':
        drugbank_sm.to_csv(
            savepath+'/drugbank_small_molecule.csv', index=False)

    print('small molecule file processed!')

    # extract protein info

    print(f'{xmlfile} processe complete!')
'''
从drugbank中获取drug-protein相关信息
'''
def parse_drug_protein_from_drugbank(xmlfile, savepath, filename, savetype='excel',geneid_file=None):
    import xml.etree.ElementTree as ET
    import collections
    import json
    import pandas
    save_file = '{}/{}'.format(savepath, filename)
    tail = xmlfile[-3:]
    print(f'process file: {xmlfile}')
    if tail == 'zip':
        import zipfile
        with zipfile.ZipFile(xmlfile) as zipfile:
            f = zipfile.open(xmlfile.split('/')[-1].strip('.zip'))
            tree = ET.parse(f)
            f.close()
    elif '.gz'==tail:
        import gzip
        with gzip.open(xmlfile) as f:
            tree=ET.parse(f)
    else:
        with open(xmlfile) as f:
            tree = ET.parse(f)
    print('read complete!')
    root = tree.getroot()  
    ns = '{http://www.drugbank.ca}'
    protein_rows = list()
    for i, drug in enumerate(root):
        drugbank_id = drug.findtext(ns + "drugbank-id[@primary='true']")
        for category in ['target', 'enzyme', 'carrier', 'transporter']:
            proteins = drug.findall('{ns}{cat}s/{ns}{cat}'.format(ns=ns, cat=category))
            for protein in proteins:
                row = {'drugbank_id': drugbank_id, 'category': category}
                row['organism'] = protein.findtext('{}organism'.format(ns))
                row['known_action'] = protein.findtext('{}known-action'.format(ns))
                actions = protein.findall('{ns}actions/{ns}action'.format(ns=ns))
                row['actions'] = '|'.join(action.text for action in actions)
                uniprot_ids = [polypep.text for polypep in protein.findall(
                    "{ns}polypeptide/{ns}external-identifiers/{ns}external-identifier[{ns}resource='UniProtKB']/{ns}identifier".format(ns=ns))]            
                if len(uniprot_ids) != 1:
                    continue
                row['uniprot_id'] = uniprot_ids[0] 
                # refs=protein.findall('{ns}references/{ns}reference'.format(ns=ns))
                # ref_text='|'.join(ref.text for ref in refs)
                # #ref_text = protein.findtext("{ns}references[@format='textile']".format(ns=ns))
                # if ref_text:

                #     pmids = re.findall(r'pubmed/([0-9]+)', ref_text)
                #     row['pubmed_ids'] = '|'.join(pmids)
                protein_rows.append(row)
    protein_df = pandas.DataFrame.from_dict(protein_rows)
    if geneid_file:   
        with gzip.open(geneid_file) as f:
            text = io.TextIOWrapper(f)
            uniprot_df = pandas.read_table(text, engine='python')
            uniprot_df.rename(columns={'uniprot': 'uniprot_id', 'GeneID': 'entrez_gene_id'}, inplace=True)

        # merge uniprot mapping with protein_df
        protein_df = protein_df.merge(uniprot_df, how='inner')
    #存储        
    if savetype=='excel':
        protein_df.to_excel(save_file,index=False)
    elif savetype=='csv':
        protein_df.to_csv(save_file,index=False)



'''
uniprot id到gene id的映射
'''
def uniprotid_to_geneid(uniprot_list,savepath,filename,savetype='csv'):
    UniprotToOtherDB(uniprot_list, savepath, filename, tran='P_ENTREZGENEID', savetype=savetype)

'''
@description: 从drug info文件中获取字典型数据
@param {type} drug info文件
@return: 
'''
def get_drugs_info(filename):
    import pandas as pd
    db=dict()
    
    df=pd.read_csv(filename)
    data=df.to_dict(orient='records')
    for d in data:
        temp=dict()
        temp['name']=d['name']
        temp['type']=d['type']
        temp['description']=d['description']
        temp['indication']=d['indication']
        temp['groups']=d['groups']
        temp['smiles']=d['smiles']
        db[d['drugbank_id'].strip()]=temp
    return db

def generate_dti_examples(fastafile,druginfo_file,save_path,filename,savetype='csv'):
    import pandas as pd
    filename='{}/{}'.format(save_path,filename)
    file=open('drug_target_examples.csv','w',newline='')
    db=drug_info(druginfo_file)
    targets=dict()
    target_seq=dict()
    drug_set=set()
    pos_pair=set()
    pairs=list()
    print('----begin----')
    with open(filename,'r') as f:
        for seq in SeqIO.parse(f,'fasta'):
            temp=dict()
            temp['Target ID']=seq.id.split('|')[-1]
            targets[temp['Target ID']]=0
            temp['Sequence']=seq.seq
            target_seq[temp['Target ID']]=seq.seq
            p=re.compile(r'[(](.*?)[)]',re.S)  #贪婪匹配括号里的内容
            drugs=re.findall(p,seq.description)[-1]
            drugs_s=drugs.split(';')
            for drug_id in drugs_s:
                drug_id=drug_id.strip()
                pos_pair.add((seq.seq,drug_id))
                drug_set.add(drug_id)
                temp['Drug ID']=drug_id
                if pd.isnull(db[drug_id]['smiles']):
                    continue
                temp['SMILES']=db[drug_id]['smiles']
                targets[temp['Target ID']]+=1
                temp['Label']=1
                pairs.append(temp)
    print('----ending----')
    drug_list=list(drug_set)
    for t in targets:
        temp=dict()
        temp['Target ID']=t
        temp['Sequence']=target_seq[t]
        
        for i in range(targets[t]):
            
            d=random.choice(drug_list)
            while (t,d) in pos_pair or pd.isnull(db[d]['smiles']):
                d=random.choice(drug_list)
            
            pos_pair.add((t,d))
            temp['Drug ID']=d
            temp['Label']=0
            temp['SMILES']=db[d]['smiles']
            pairs.append(temp)
    print('----ending----')

'''
生物数据库之间的映射
src_compound_id : 源数据库，比如，chebi->7
src_id: 目标数据库 如 drugbank->2
'''
def database_map_by_id(src_compound_id,src_id,save_path,filename,savetype='tsv'):
    import json
    import pandas as pd
    filename='{}/{}'.format(save_path,filename)
    # 此列表会更新：https://www.ebi.ac.uk/unichem/ucquery/listSources
    id_to_source = {
        0: None,
        1: 'chembl',
        2: 'drugbank',
        3: 'pdb',
        4: 'iuphar',
        5: 'pubchem_dotf',
        6: 'kegg_ligand',
        7: 'chebi',
        8: 'nih_ncc',
        9: 'zinc',
        10: 'emolecules',
        11: 'ibm',
        12: 'atlas',
        13: 'ibm_patents',
        14: 'fdasrs',
        15: 'surechembl',
        17: 'pharmgkb',
        18: 'hmdb',
        20: 'selleck',
        21: 'pubchem_tpharma',
        22: 'pubchem',
        23: 'mcule',
        24: 'nmrshiftdb2',
        25: 'lincs',
        26: 'actor',
        27: 'recon',
        28: 'molport',
        29: 'nikkaji',
        31: 'bindingdb',
        32: 'comptox',
        33:	'lipidmaps',
        34:	'drugcentral',
        35:	'carotenoiddb',
        36:	'metabolights',
        37:	'brenda',
        38:	'rhea',
        39:	'chemicalbook',
        40:	'dailymed',
        41:	'swisslipids',
        45:	'dailymed_new',
        46:	'clinicaltrials'
    }
    url='https://www.ebi.ac.uk/unichem/rest/mapping/{}/{}'.format(src_compound_id,src_id)
    data=get_data_by_url(url)
    data=json.loads(data)
    map_list=list()
    
    for line in data:
        temp=dict()
        temp[id_to_source[src_compound_id]]=line[str(src_compound_id)]
        temp[id_to_source[src_id]]=line[str(src_id)]
        map_list.append(temp)
    data=pd.DataFrame(map_list)
    if savetype=='tsv':
        data.to_csv(filename,sep='\t',index=False)
    elif savetype=='excel':
        data.to_excel(filename,index=False)
    else:
        data.to_csv(filename,index=False)
    
if __name__ == "__main__":
    log = logger('logs')
    # SaveSDF('DB001','./',log)

    # SaveDrugInfo(['DB00001','DB06605'],'test','drug_list.xlsx',log,file_type='excel')

    # UniprotToOtherDB(['P40925','Q07817'],'./','p_gene.csv')
    database_map_by_id(2,7,'BioDb/drugbank', 'drugbank_chebi.tsv')
    #parse_drugs_drugbank('BioDb/drugbank/fulldatabase.xml.zip','BioDb/drugbank','drugs_info.csv',savetype='csv')
    get_drugs_info('BioDb/drugbank/drugs_info.csv')
    #parse_drug_protein_from_drugbank('BioDb/drugbank/fulldatabase.xml.zip','BioDb/drugbank','drug_proteins.csv',savetype='csv')
    # drug_map_to('BioDb/drugbank/drugs_info.csv',
    #             'BioDb/drugbank', 'mapping.tsv.gz', log)
