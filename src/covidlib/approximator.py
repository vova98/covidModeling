# -*- coding: utf-8 -*-
from abc import ABC
from scipy.interpolate import interp1d
import datetime
import numpy as np
from sklearn.linear_model import Ridge


class Approximator(ABC):
    r"""Базовый класс для всех аппроксимирующих моделей."""
    _name = 'NotImplementedError'
    _parameters = dict()

    def __init__(self):
        pass

    def fit(self, data):
        r"""
        Данная функция должна аппроксимировать выборку для полученных данных.
        Под аппроксимацией подрозумевается настройка всех параметров модели.

        :param data: Словарь вида
                key - номер объекта,
                value словарь {'date': строка в формате day.month.year,
                               'sick': int,
                               'recovered': int,
                               'died': int}
        :type data: dict
        """
        raise NotImplementedError

    def predict(self, date):
        r"""
        Данная функция должна возвращать предсказания для данной даты.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str

        :return: Словарь вида {'date': строка в формате day.month.year,
                               'sick': int,
                               'recovered': int,
                               'died': int}
        :type data: dict
        :rtype: dict
        """
        raise NotImplementedError

    def predict_between(self, date_from, date_to):
        r"""
        Данная функция должна возвращать предсказания для всех дат между
            адаными.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str

        :return: список словарей вида:
        {
            'date': строка в формате day.month.year,
            'sick': int,
            'recovered': int,
            'died': int
        }
        :rtype: list
        """
        raise NotImplementedError


class SplineApproximator(Approximator):
    r"""
    Простая реализация аппроксиматора на основе сплайнов.
    """
    _name = 'Сплайны'
    _parameters = {'kind': {
        'description': 'Тип кривой для построение сплайнов:'
                       ' кубическая либо линейная.',
        'type': 'choise',
        'values': ['cubic', 'linear'],
        'default': 'cubic',
        'min': None,
        'max': None}}

    def __init__(self, kind='cubic'):
        super(SplineApproximator, self).__init__()

        self.kind = kind
        self.approximators = dict()

    def fit(self, data):
        r"""
        Данная функция должна аппроксимировать выборку для полученных данных.
        Под аппроксимацией подрозумевается настройка всех параметров модели.
        Предполагается, что все дни представлены в выборки.

        :param data: Словарь вида
                key - номер объекта,
                value словарь {'date': строка в формате day.month.year,
                               'sick': int,
                               'recovered': int,
                               'died': int}
        :type data: dict
        """
        models = ['sick', 'recovered', 'died']

        points = sorted(list(data.keys()))
        for model in models:
            y = [data[p][model] for p in points]
            x = [datetime.datetime.strptime(data[p]['date'], '%d.%m.%Y').timestamp() for p in points]
            self.approximators[model] = interp1d(x, y, kind=self.kind,
                                                 fill_value="extrapolate")

    def predict(self, date):
        r"""
        Данная функция должна возвращать предсказания для данной даты.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str
        """
        pred_date = datetime.datetime.strptime(date, '%d.%m.%Y').timestamp()

        ret = dict()
        ret['date'] = date
        for key in self.approximators:
            ret[key] = self.approximators[key](pred_date).tolist()

        return ret

    def predict_between(self, date_from, date_to):
        r"""
        Данная функция должна возвращать предсказания для всех дат между
            адаными.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str

        :return: список словарей вида:
        {
            'date': строка в формате day.month.year,
            'sick': int,
            'recovered': int,
            'died': int
        }
        :rtype: list
        """
        date_from = datetime.datetime.strptime(date_from, '%d.%m.%Y')
        date_to = datetime.datetime.strptime(date_to, '%d.%m.%Y')

        cur_date = date_from

        list_of_ret = []
        while cur_date <= date_to:
            pred = self.predict(cur_date.strftime('%d.%m.%Y'))
            cur_date = cur_date + datetime.timedelta(days=1)

            list_of_ret.append(pred)

        return list_of_ret


class LinearApproximator(Approximator):
    r"""
    Простая реализация аппроксиматора на основе линейной регрессии.
    """
    _name = 'МНК'
    _parameters = {'alpha': {
        'description': 'Параметр регуляризации alpha.'
                       ' В диапазоне от 0 до 1000.',
        'type': 'continues',
        'values': [],
        'default': '1.0',
        'min': '0.0',
        'max': '1000.0'}}

    def __init__(self, alpha=1.0):
        super(LinearApproximator, self).__init__()

        self.alpha = float(alpha)
        if self.alpha < float(self._parameters['alpha']['min']):
            self.alpha = float(self._parameters['alpha']['min'])
        if self.alpha > float(self._parameters['alpha']['max']):
            self.alpha = float(self._parameters['alpha']['max'])
        self.approximators = dict()

    def fit(self, data):
        r"""
        Данная функция должна аппроксимировать выборку для полученных данных.
        Под аппроксимацией подрозумевается настройка всех параметров модели.
        Предполагается, что все дни представлены в выборки.

        :param data: Словарь вида
                key - номер объекта,
                value словарь {'date': строка в формате day.month.year,
                               'sick': int,
                               'recovered': int,
                               'died': int}
        :type data: dict
        """
        models = ['sick', 'recovered', 'died']

        points = sorted(list(data.keys()))
        for model in models:
            y = [data[p][model] for p in points]
            x = np.array([datetime.datetime.strptime(
                    data[p]['date'], '%d.%m.%Y').timestamp() for p in points]).reshape([-1, 1])
            self.approximators[model] = Ridge(self.alpha)
            self.approximators[model].fit(np.reshape(x, [-1, 1]), y)


    def predict(self, date):
        r"""
        Данная функция должна возвращать предсказания для данной даты.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str
        """
        pred_date = datetime.datetime.strptime(date, '%d.%m.%Y').timestamp()

        ret = dict()
        ret['date'] = date
        for key in self.approximators:
            ret[key] = self.approximators[key].predict([[pred_date]]).tolist()

        return ret

    def predict_between(self, date_from, date_to):
        r"""
        Данная функция должна возвращать предсказания для всех дат между
            адаными.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str

        :return: список словарей вида:
        {
            'date': строка в формате day.month.year,
            'sick': int,
            'recovered': int,
            'died': int
        }
        :rtype: list
        """
        date_from = datetime.datetime.strptime(date_from, '%d.%m.%Y')
        date_to = datetime.datetime.strptime(date_to, '%d.%m.%Y')

        cur_date = date_from

        list_of_ret = []
        while cur_date <= date_to:
            pred = self.predict(cur_date.strftime('%d.%m.%Y'))
            cur_date = cur_date + datetime.timedelta(days=1)
            
            list_of_ret.append(pred)

        return list_of_ret

class NesterovConstantGamma(Approximator):
    r"""
    Реализация метода Нестерова, в случае фиксированых параметров \Delta и \gamma
    """
    _name = 'Нестеров с постоянными параметрами'
    _parameters = {'gamma': {
        'description': 'Ежедневная скорость заражения'
                       ' В диапазоне от 0. до 10.',
        'type': 'continues',
        'values': [],
        'default': '1.0',
        'min': '0.0',
        'max': '10.0'},
        'delta': {
        'description': 'Параметр задержки заболевения.'
                       ' В диапазоне от 1 до 30',
        'type': 'continues',
        'values': [],
        'default': '10',
        'min': '1',
        'max': '30'}}

    def __init__(self, gamma=1.0, delta=10):
        super(NesterovConstantGamma, self).__init__()

        self.gamma = float(gamma)
        if self.gamma < float(self._parameters['gamma']['min']):
            self.gamma = float(self._parameters['gamma']['min'])
        if self.gamma > float(self._parameters['gamma']['max']):
            self.gamma = float(self._parameters['gamma']['max'])
        
        self.delta = int(delta)
        if self.delta < int(self._parameters['delta']['min']):
            self.delta = int(self._parameters['delta']['min'])
        if self.delta > int(self._parameters['delta']['max']):
            self.delta = int(self._parameters['delta']['max'])

    def fit(self, data):
        r"""
        Данная функция должна аппроксимировать выборку для полученных данных.
        Под аппроксимацией подрозумевается настройка всех параметров модели.
        Предполагается, что все дни представлены в выборки.

        :param data: Словарь вида
                key - номер объекта,
                value словарь {'date': строка в формате day.month.year,
                               'sick': int,
                               'recovered': int,
                               'died': int}
        :type data: dict
        """

        self.dict_of_data = dict()

        for key in data:
            date = datetime.datetime.strptime(data[key]['date'], '%d.%m.%Y').date()
            if date not in self.dict_of_data:
                self.dict_of_data[date] = dict()
            self.dict_of_data[date]['new sick'] = data[key]['sick']
            
        # Надобы обработать пропуск значений
            
        for key in self.dict_of_data:
            self.dict_of_data[key]['sick'] = self.dict_of_data.get(
                key - datetime.timedelta(days=1), {'sick': 0})['sick'] + self.dict_of_data[key]['new sick'] 

        for key in self.dict_of_data:
            self.dict_of_data[key]['gamma'] = self.gamma
            self.dict_of_data[key]['delta'] = self.delta




    def predict(self, date):
        r"""
        Данная функция должна возвращать предсказания для данной даты.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str

        return: ссловарь вида:
        {
            'date': строка в формате day.month.year,
            'sick': int,
            'recovered': int,
            'died': int
        }
        :rtype: dict
        """
        date = datetime.datetime.strptime(date, '%d.%m.%Y').date()

        cur_date = max(self.dict_of_data) + datetime.timedelta(days=1)
        while cur_date <= date:
            self.dict_of_data[cur_date] = dict()
            self.dict_of_data[cur_date]['gamma'] = self.gamma
            self.dict_of_data[cur_date]['delta'] = self.delta
            
            self.dict_of_data[cur_date]['new sick'] = int(
                self.dict_of_data.get(
                    cur_date-datetime.timedelta(days=self.dict_of_data[cur_date]['delta']), 
                    {'gamma': self.gamma})['gamma']\
                *(
                    self.dict_of_data.get(
                        cur_date-datetime.timedelta(days=1), 
                        {'sick': 0})['sick'] \
                    - self.dict_of_data.get(
                        cur_date-datetime.timedelta(days=self.dict_of_data[cur_date]['delta']+1), 
                        {'sick': 0})['sick']))
            
            self.dict_of_data[cur_date]['sick'] = self.dict_of_data.get(
                cur_date-datetime.timedelta(days=1), 
                {'sick': 0})['sick'] + self.dict_of_data[cur_date]['new sick']
            
            cur_date = cur_date + datetime.timedelta(days=1)
    

        return {'date': date.strftime('%d.%m.%Y'), 
                'sick': self.dict_of_data[date]['new sick'], 
                'recovered': 0, 
                'died': 0}

    def predict_between(self, date_from, date_to):
        r"""
        Данная функция должна возвращать предсказания для всех дат между
            адаными.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str

        :return: список словарей вида:
        {
            'date': строка в формате day.month.year,
            'sick': int,
            'recovered': int,
            'died': int
        }
        :rtype: list
        """
        date_from = datetime.datetime.strptime(date_from, '%d.%m.%Y')
        date_to = datetime.datetime.strptime(date_to, '%d.%m.%Y')

        cur_date = date_from

        list_of_ret = []
        while cur_date <= date_to:
            pred = self.predict(cur_date.strftime('%d.%m.%Y'))
            cur_date = cur_date + datetime.timedelta(days=1)
            
            list_of_ret.append(pred)

        return list_of_ret
