# -*- coding: utf-8 -*-
from copy import deepcopy
from datetime import datetime, timedelta
import inspect
import json
import hashlib
from functools import lru_cache
from pathlib import Path
import re

import boto3
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
import pandas as pd
import requests

import covidlib

Yandex_data_path = Path('data/Cities_to_22_10.csv').resolve()
Name_mapping_path = Path('data/mapping.txt').resolve()


def hashing(city):
    return int(hashlib.sha1(city.encode('cp1251')).hexdigest(), 16) % (10 ** 6)


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


def init_base():
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
        yandex_data = pd.read_csv(Yandex_data_path, delimiter=';')

        list_of_cities = yandex_data['region'].unique()
        for city_num, city in enumerate(list_of_cities):
            data_for_city = yandex_data[
                yandex_data['region'] == city].to_numpy()
            data = {}
            for idx, row in enumerate(data_for_city):
                data[idx] = {'date': row[0],
                             'died': row[5],
                             'sick': row[6],
                             'recovered': row[7]}
            try:
                cities.put_item(
                    Item={'id': str(hashing(city)),
                          'name': city,
                          'from': data[0]['date'],
                          'to_': data[data_for_city.shape[0] - 1]['date'],
                          'data_': json.dumps(data)})
            except ClientError as e:
                print(e.response['Error']['Message'])
        cities.put_item(
            Item={'id': str('-1'),
                  'ID': 15752,
                  'date_': '22.10.2020'})

    except Exception:
        cities = dynamodb.Table('cities')
        pass


def map_names():
    mapping = {}
    with open(Name_mapping_path) as file:
        for line in file:
            from_news, from_yandex = line[:-1].split(':')
            mapping[from_news] = from_yandex
    return mapping


def parse_page(soup, mapping, cities_table):
    date = soup.find('p', {'class': 'date'}).text[:-3]
    data = soup.find('div', {'class': 'news-detail'}).text.split('\n')
    for line in data:
        result = re.search(r'\d+\. ([\w ()-]+) - (\d+)', line)
        if result is not None:
            city_name = result.group(1) if result.group(1) not in mapping \
                else mapping[result.group(1)]
            new_record = {'date': date,
                          'died': 0,
                          'sick': result.group(2),
                          'recovered': 0}
            city_id = hashing(city_name)
            try:
                get_city = cities_table.get_item(Key={'id': str(city_id)})
                if 'Item' not in get_city:
                    print('bad city name', result.group(1))
                    continue
                data_from_base = json.loads(get_city['Item']['data_'])

                data_from_base[len(data_from_base.keys())] = new_record

                cities_table.update_item(
                    Key={
                        'id': str(city_id)
                    },
                    UpdateExpression="set to_=:date, data_=:data",
                    ExpressionAttributeValues={
                        ':date': date,
                        ':data': json.dumps(data_from_base)
                    },
                    ReturnValues="UPDATED_NEW"
                )
            except ClientError as e:
                print(e.response['Error']['Message'])
    return date


def update_data():
    print('start of update')
    url = 'https://www.rospotrebnadzor.ru/about/info/news/news_details.php?' \
          'ELEMENT_ID=%d'
    right_article_name = ' О подтвержденных случаях новой коронавирусной ' \
                         'инфекции COVID-2019 в России'

    dynamodb = DynamoDBSingleton.get()
    cities_table = dynamodb.Table('cities')
    ID_item = cities_table.get_item(Key={'id': '-1'})
    ID = ID_item['Item']['ID'] + 1
    date = ID_item['Item']['date_']
    yesterday = datetime.today() - timedelta(days=1)

    mapping = map_names()
    while pd.to_datetime(date).date() < yesterday.date():
        page = requests.get(url % ID)
        soup = BeautifulSoup(page.text, features='lxml')
        header = soup.find('h1').text
        if header == right_article_name:
            date = parse_page(soup, mapping, cities_table)
            try:
                cities_table.update_item(
                    Key={
                        'id': '-1'
                    },
                    UpdateExpression="set ID=:ID, date_=:date",
                    ExpressionAttributeValues={
                        ':ID': ID,
                        ':date': date
                    },
                    ReturnValues="UPDATED_NEW"
                )
            except ClientError as e:
                print(e.response['Error']['Message'])
        ID = ID + 1
    print('end of update')
    return date


def prune_data(data, use_date_from, use_date_to):
    use_date_from = datetime.strptime(use_date_from, '%d.%m.%Y')
    use_date_to = datetime.strptime(use_date_to, '%d.%m.%Y')

    new_data = dict()
    for key in data:
        cur_date = datetime.strptime(data[key]['date'], '%d.%m.%Y')
        if use_date_from <= cur_date and cur_date <= use_date_to:
            new_data[key] = data[key]

    return new_data


@lru_cache(maxsize=10 ** 8)
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

    return response['Item']['from'], response['Item']['to_']


def get_cities():
    dynamodb = DynamoDBSingleton.get()
    table = dynamodb.Table('cities')
    ret = table.scan()['Items']
    return {item['id']: item['name'] for item in ret if 'name' in item.keys()}


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
