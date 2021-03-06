# -*- coding: utf-8 -*-
from copy import deepcopy
from datetime import datetime, timedelta
import inspect
import json
import sys
import os
import hashlib
import logging
from functools import lru_cache
from pathlib import Path
import re

import boto3
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
import pandas as pd
import requests

import covidlib

yandex_data_path = Path('data/dump_cities.csv').resolve()
cities_codes_path = Path('data/mapping.json').resolve()

class DynamoDBSingleton(object):
    _dynamodb = None

    @staticmethod
    def load():
        DynamoDBSingleton._dynamodb = boto3.resource(
            'dynamodb',
            region_name="us-west-2",
            endpoint_url="http://localhost:8000")
        return DynamoDBSingleton._dynamodb

    @staticmethod
    def get():
        if DynamoDBSingleton._dynamodb is not None:
            return DynamoDBSingleton._dynamodb
        else:
            return DynamoDBSingleton.load()

class LoggerSinglton(object):
    _init = False

    @staticmethod
    def init():
        if not LoggerSinglton._init:
            LoggerSinglton._init = True
            logging.basicConfig(filename='logs.log',
                    level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d %(levelname)s:%(funcName)s:%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
            logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

def init_base():
    LoggerSinglton.init()
    logging.info('init database')

    dynamodb = DynamoDBSingleton.get()
    try:
        cities = dynamodb.create_table(
            TableName='cities',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        meta = dynamodb.create_table(
            TableName='meta',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
    except Exception:
        logging.info('load database from checkpoint')
        cities = dynamodb.Table('cities')
        meta = dynamodb.Table('meta')
        return

    yandex_data = pd.read_csv(yandex_data_path, delimiter=';')
    with open(cities_codes_path) as f:
        cities_codes = json.load(f)
    
    inverse_index = dict()
    for key in cities_codes:
        inverse_index[cities_codes[key]['yandex_name']] = key

    for city in yandex_data['region'].unique():
        if city in inverse_index:
            data_for_city = yandex_data[
                yandex_data['region'] == city].to_numpy()
            data = {}
            for row in data_for_city:
                data[data.__len__()] = {'date': row[0],
                                      'died': row[5],
                                      'sick': row[6],
                                      'recovered': row[7]}
            last_date = data[data.__len__() - 1]['date']
            cities.put_item(
                Item={'id': inverse_index[city],
                      'name': cities_codes[inverse_index[city]]['name'],
                      'from_': data[0]['date'],
                      'to_': last_date,
                      'data_': json.dumps(data)})

    meta.put_item(
        Item={'id': 'update',
              'date_': datetime.strptime(
                last_date, 
                '%d.%m.%Y').strftime('%S.%M.%H.%d.%m.%Y'),
              'last_try_': datetime.strptime(
                last_date, 
                '%d.%m.%Y').strftime('%S.%M.%H.%d.%m.%Y')})

    logging.info('init new database')

def update_by_stopcoronavirus():
    LoggerSinglton.init()
    logging.info('start parse stopcoronavirus')
    dynamodb = DynamoDBSingleton.get()
    cities_table = dynamodb.Table('cities')
    meta_table = dynamodb.Table('meta')

    url = 'https://стопкоронавирус.рф/covid_data.json?do=region_stats&code={}'

    cities = get_cities()
    
    for key in cities:
        logging.info('load info for {}'.format(key))

        city_item = cities_table.get_item(Key={'id': key})
        if 'Item' not in city_item:
            logging.info('bad city {}'.foramat(key))
            continue

        to_ = datetime.strptime(city_item['Item']['to_'], '%d.%m.%Y')
        data_ = json.loads(city_item['Item']['data_'])

        if to_.date() >= datetime.today().date():
            logging.info('nothing to update for {}'.format(key))
            continue

        page = requests.get(url.format(key))
        info = page.json()
        for item in info:
            item['date'] = datetime.strptime(item['date'], '%d.%m.%Y')
            item['sick'] = int(item['sick'])
            item['healed'] = int(item['healed'])
            item['died'] = int(item['died'])
            
        info = sorted(info, key=lambda x: x['date'])

        for i in range(1, len(info)):
            info[i]['sick_inc'] = info[i]['sick'] - info[i-1]['sick']
            info[i]['healed_inc'] = info[i]['healed'] - info[i-1]['healed']
            info[i]['died_inc'] = info[i]['died'] - info[i-1]['died']
            
        info = info[1:]
        flag = False
        for item in info:
            if item['date'] > to_:
                data_[data_.__len__()] = {'date': item['date'].strftime('%d.%m.%Y'),
                                        'died': item['died_inc'],
                                        'sick': item['sick_inc'],
                                        'recovered': item['healed_inc']}
                to_ = item['date']
                flag = True
        
        if flag:
            logging.info('update info for {}'.format(key))
            cities_table.update_item(
                Key={'id': key},
                UpdateExpression="set to_=:date, data_=:data",
                ExpressionAttributeValues={
                    ':date': to_.strftime('%d.%m.%Y'),
                    ':data': json.dumps(data_)},
                ReturnValues="UPDATED_NEW")

            meta_table.update_item(
                Key={'id': 'update'},
                UpdateExpression="set date_=:date",
                ExpressionAttributeValues={
                    ':date': datetime.today().strftime('%S.%M.%H.%d.%m.%Y')
                },
                ReturnValues="UPDATED_NEW"
            )
        else:
            logging.info('nothing to update for {}'.format(key))

    logging.info('end parse stopcoronavirus')
    return {}

def update_data(type_='stopcoronavirus'):
    r"""
    Обновляет данные в базе данных на основе заданого сайта. 
    Работает на основе сайта стопкоронавирус.рф

    :param type_: тип обновления базы данных
    :type type_: str
    """
    LoggerSinglton.init()
    logging.info('start of update')

    dynamodb = DynamoDBSingleton.get()
    meta_table = dynamodb.Table('meta')

    last_try_ = meta_table.get_item(Key={'id': 'update'})
    time = last_try_['Item']['last_try_']
    time = datetime.strptime(time, '%S.%M.%H.%d.%m.%Y')
    current_time = datetime.today()

    ret = {}
    if (current_time - time).seconds > 3600:
        logging.info('previous try = {}, now = {}'.format(
            time.strftime('%S:%M:%H/%d.%m.%Y'), 
            current_time.strftime('%S:%M:%H/%d.%m.%Y')))
        meta_table.update_item(
            Key={'id': 'update'},
            UpdateExpression="set last_try_=:date",
            ExpressionAttributeValues={
                ':date': current_time.strftime('%S.%M.%H.%d.%m.%Y')
            },
            ReturnValues="UPDATED_NEW"
        )
        if type_ == 'stopcoronavirus':
            ret = update_by_stopcoronavirus()
    else:
        logging.info('too frequent database update request')
        ret = {}

    logging.info('end of update')
    return ret

def prune_data(data, use_date_from, use_date_to):
    r"""

    """
    use_date_from = datetime.strptime(use_date_from, '%d.%m.%Y')
    use_date_to = datetime.strptime(use_date_to, '%d.%m.%Y')

    new_data = dict()
    for key in data:
        cur_date = datetime.strptime(data[key]['date'], '%d.%m.%Y')
        if use_date_from <= cur_date and cur_date <= use_date_to:
            new_data[key] = data[key]

    return new_data

def approximate(city, models, date):
    r"""
    :param city: город для аппроксимации
    :type city: str

    :param models: словарь моделей с параметрами в формате JSON,
        json чтобы можно было в кеш записать все
    :type models: json

    :param date: набор дат, которые нужны для построения и инферена модели
    :type date: json
    """
    dynamodb = DynamoDBSingleton.get()
    meta_table = dynamodb.Table('meta')
    update = meta_table.get_item(Key={'id': 'update'})
    time = update['Item']['date_']
    return _approximate(city, models, date, time)

@lru_cache(maxsize=10 ** 8)
def _approximate(city, models, date, time):
    r"""
    :param city: город для аппроксимации
    :type city: str

    :param models: словарь моделей с параметрами в формате JSON,
        json чтобы можно было в кеш записать все
    :type models: json

    :param date: набор дат, которые нужны для построения и инферена модели
    :type date: json

    :param time: время последнего обновления базы 
        (данная фича позволяет не включить кеш, если база была обновлена)
    :type time: str
    """
    models = json.loads(models)
    date = json.loads(date)
    worked_models = get_models()

    data = get_city_statistic(city)

    datas = dict()
    datas['real'] = deepcopy(data)

    for mod in models:
        datas[mod] = deepcopy(data)
        datas[mod] = prune_data(
            datas[mod], date['use_date_from'], date['use_date_to'])

        model = worked_models[mod]['model'](**models[mod]['parameters'])
        model.fit(datas[mod])

        datas[mod] = dict()
        preds = model.predict_between(
            (datetime.strptime(date['use_date_to'], '%d.%m.%Y')
                + timedelta(days=1)).strftime('%d.%m.%Y'),
            date['predict_date_to'])

        for pred in preds:
            datas[mod][datas[mod].__len__()] = pred

    return datas


def get_dates(city):
    dynamodb = DynamoDBSingleton.get()
    table = dynamodb.Table('cities')
    response = table.get_item(Key={'id': city})

    if 'Item' not in response:
        return '01.01.2020', '01.10.2020'

    return response['Item']['from_'], response['Item']['to_']

def scan_table(table):
    response = table.scan()
    yield from response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        yield from response['Items']

def get_stats():
    dynamodb = DynamoDBSingleton.get()
    table = dynamodb.Table('cities')

    cities = dict()
    for item in scan_table(table):
        cities[item['id']] = dict()
        cities[item['id']]['name'] = item['name']
        cities[item['id']]['from'] = item['from_']
        cities[item['id']]['to'] = item['to_']

    return cities

def get_cities():
    dynamodb = DynamoDBSingleton.get()
    table = dynamodb.Table('cities')

    cities = dict()

    cities = dict()
    for item in scan_table(table):
        cities[item['id']] = item['name']

    cities = {key: cities[key] for key in sorted(cities)}

    sorted_cities = {'RU-MOW': cities['RU-MOW'],
                     'RU-MOS': cities['RU-MOS'],
                     'RU-SPE': cities['RU-SPE']}
    sorted_cities.update(
        {key: cities[key]  for key in sorted(cities) if key not in {'RU-MOW', 'RU-MOS', 'RU-SPE'}})

    return sorted_cities


def get_models(with_approximator=True):
    models_modules = dict()
    for cls_name, cls_obj in inspect.getmembers(covidlib):
        try:
            if cls_obj.__module__ == covidlib.approximator.__name__:
                models_modules[cls_name] = cls_obj
        except Exception:
            continue

    models = dict()
    for key in models_modules:
        models[key] = dict()
        models[key]['name'] = models_modules[key]._name
        if with_approximator:
            models[key]['model'] = models_modules[key]
        models[key]['parameters'] = models_modules[key]._parameters
    return models


def get_city_statistic(city):
    r"""
    Возвращает данные для соответствующего города

    :param city: город для которого вернуть данные
    :type city: str

    :return: вовзращает данные для соответсвующего города.
             данные это словарь
                key - номер объекта,
                value словарь {'date': строка в формате day.month.year,
                               'sick': int,
                               'recovered': int,
                               'died': int}
    :rtype: dict
    """
    dynamodb = DynamoDBSingleton.get()
    table = dynamodb.Table('cities')
    response = table.get_item(Key={'id': city})

    if 'Item' not in response:
        return dict()
    load = json.loads(response['Item']['data_'])

    dict_ = dict()
    for key in load:
        dict_[int(key)] = load[key]

    return dict_


def get_data_field():
    r"""
    Возвращает рассматриваемые моделью поля.
    В нашем случае возвращает словарь {'sick': 'Заболело',
                                       'recovered': 'Выздоровело',
                                       'died': 'Умерло'}

    :return: словрь релевантных полей данных.
    :rtype: dict
    """
    return {'sick': 'Заболело',
            'recovered': 'Выздоровело',
            'died': 'Умерло'}
