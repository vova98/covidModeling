# -*- coding: utf-8 -*-
import numpy as np
import json
from functools import lru_cache

import inspect
import covidlib
from copy import deepcopy

import boto3


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
    def data_insert(y):
        data = dict()
        for i in range(1, 30):
            data[i] = dict()
            data[i]['date'] = '{}.9.2020'.format(i)
            data[i]['sick'] = y[i]
            data[i]['recovered'] = np.random.randint(1, 100)
            data[i]['died'] = np.random.randint(1, 100)
        return data

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

        np.random.seed(42)
        x = np.linspace(2, 5, 30)
        y = 100*(np.sin(10*x)+1)/x + np.random.randn(30)
        dict_ = data_insert(y)

        cities.put_item(
            Item={'id': 'test1',
                  'name': 'Тестовый город 1',
                  'from': dict_[1]['date'],
                  'to': dict_[29]['date'],
                  'data': json.dumps(dict_)})

        np.random.seed(0)
        x = np.linspace(2, 5, 30)
        y = (np.exp(x)+1)/x + np.random.randn(30)
        dict_ = data_insert(y)

        cities.put_item(
            Item={'id': 'test2',
                  'name': 'Тестовый город 2',
                  'from': dict_[1]['date'],
                  'to': dict_[29]['date'],
                  'data': json.dumps(dict_)})
    except Exception:
        cities = dynamodb.Table('cities')
        pass


@lru_cache(maxsize=10**8)
def approximate(city, models, date):
    r"""
    :param city: город для аппроксимации
    :type city: str

    :param models: список моделей
    :type models: list

    :param date: дата к которой нужно аппроксимировать
    :type date: str
    """
    worked_models = get_models()

    data = get_city_statistic(city)

    datas = dict()
    datas['real'] = deepcopy(data)

    for mod in models:
        datas[mod] = deepcopy(data)
        model = worked_models[mod]['model']()
        model.fit(datas[mod])

        for key in datas[mod]:
            datas[mod][key] = model.predict(datas[mod][key]['date'])

        if date:
            for pred in model.predict_to(date):
                datas[mod][datas[mod].__len__()+1] = pred

    return datas


def get_cities():
    dynamodb = DynamoDBSingleton.get()
    table = dynamodb.Table('cities')
    ret = table.scan()['Items']
    return {item['id']: item['name'] for item in ret}


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
    load = json.loads(response['Item']['data'])

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
