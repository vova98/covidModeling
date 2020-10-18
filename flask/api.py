# -*- coding: utf-8 -*- 
import numpy as np

from covidlib import approximator
from copy import deepcopy


def approximate(data, models, date):
    r"""
    :param data: выборка
    :type data: dict

    :param models: список моделей
    :type models: list

    :param date: дата к которой нужно аппроксимировать
    :type date: str
    """
    worked_models = get_models()

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
    return ['test1', 'test2']

def get_models():
    models = dict()
    models['spline'] = dict()
    models['spline']['name'] = 'сплайн'
    models['spline']['model'] = approximator.SplineApproximator
    models['spline']['parameters'] = dict()
    return models

def get_city_statistic(city):
    r"""
    Возвращает данные для соответствующего города

    :param country: город для которого вернуть данные
    :type country: str

    :return: вовзращает данные для соответсвующего города. 
             данные это словарь
                key - номер объекта, 
                value словарь {'date': строка в формате day.month.year,
                               'sick': int, 
                               'recovered': int,
                               'died': int}
    :rtype: dict
    """
    if city == 'test1':
        np.random.seed(42)
        x = np.linspace(2, 5, 30)
        y = 100*(np.sin(10*x)+1)/x + np.random.randn(30)
        DICT = dict()
        for i in range(1, 30):
            DICT[i] = dict()
            DICT[i]['date'] = '{}.9.2020'.format(i)
            DICT[i]['sick'] = y[i]
            DICT[i]['recovered'] = np.random.randint(1, 100)
            DICT[i]['died'] = np.random.randint(1, 100)
        return DICT
    elif city == 'test2':
        np.random.seed(0)
        x = np.linspace(2, 5, 30)
        y = (np.exp(x)+1)/x + np.random.randn(30)
        DICT = dict()
        for i in range(1, 30):
            DICT[i] = dict()
            DICT[i]['date'] = '{}.9.2020'.format(i)
            DICT[i]['sick'] = y[i]
            DICT[i]['recovered'] = np.random.randint(1, 100)
            DICT[i]['died'] = np.random.randint(1, 100)
        return DICT
