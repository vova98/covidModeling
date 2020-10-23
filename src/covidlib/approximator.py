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

    def predict_to(self, date):
        r"""
        Данная функция должна возвращать предсказания для всех дат начиная с
            последней доступной в обучении и до заданой.
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
    _name='Сплайны'
    _parameters={'kind': {'description': 'Тип кривой для построение сплайнов: кубическая либо линейная.',
                          'type': 'choise',
                          'values': ['cubic', 'linear'],
                          'default': 'cubic',
                          'min': None,
                          'max': None}}
    def __init__(self, kind='cubic'):
        super(SplineApproximator, self).__init__()
        

        self.kind = kind
        self.approximators = dict()
        self.last_fitted_element = None

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
            x = [p for p in points]
            self.approximators[model] = interp1d(x, y, kind=self.kind,
                                                 fill_value="extrapolate")

        last_point = points[-1]
        day, month, year = data[last_point]['date'].split('.')
        last_date = datetime.date(int(year), int(month), int(day))
        self.last_fitted_element = (last_point, last_date)

    def predict(self, date):
        r"""
        Данная функция должна возвращать предсказания для данной даты.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str
        """
        day, month, year = date.split('.')
        pred_date = datetime.date(int(year), int(month), int(day))
        _id = self.last_fitted_element[0] + (
                    pred_date - self.last_fitted_element[1]).days

        ret = dict()
        ret['date'] = date
        for key in self.approximators:
            ret[key] = self.approximators[key](_id).tolist()

        return ret

    def predict_to(self, date):
        r"""
        Данная функция должна возвращать предсказания для всех дат начиная с
            последней доступной в обучении и до заданой.
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

        day, month, year = date.split('.')
        pred_date = datetime.date(int(year), int(month), int(day))

        cur_date = self.last_fitted_element[1] + datetime.timedelta(days=1)

        list_of_ret = []
        while cur_date <= pred_date:
            pred = self.predict(cur_date.strftime('%d.%m.%Y'))
            cur_date = cur_date + datetime.timedelta(days=1)

            list_of_ret.append(pred)

        return list_of_ret


class LinearApproximator(Approximator):
    r"""
    Простая реализация аппроксиматора на основе линейной регрессии.
    """
    _name='МНК'
    _parameters={'alpha': {'description': 'Параметр регуляризации alpha. В диапазоне от 0 до 1000.',
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
            x = np.array([p for p in points]).reshape([-1,1])
            self.approximators[model] = Ridge(self.alpha)
            self.approximators[model].fit(np.reshape(x, [-1,1]), y)

        last_point = points[-1]
        day, month, year = data[last_point]['date'].split('.')
        last_date = datetime.date(int(year), int(month), int(day))
        self.last_fited_element = (last_point, last_date)

    def predict(self, date):
        r"""
        Данная функция должна возвращать предсказания для данной даты.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str
        """
        day, month, year = date.split('.')
        pred_date = datetime.date(int(year), int(month), int(day))
        _id = self.last_fited_element[0] + (
                pred_date - self.last_fited_element[1]).days

        ret = dict()
        ret['date'] = date
        for key in self.approximators:
            ret[key] = self.approximators[key].predict([[_id]]).tolist()[0]

        return ret

    def predict_to(self, date):
        r"""
        Данная функция должна возвращать предсказания для всех дат начиная с
            последней доступной в обучении и до заданой.
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

        day, month, year = date.split('.')
        pred_date = datetime.date(int(year), int(month), int(day))

        cur_date = self.last_fited_element[1] + datetime.timedelta(days=1)

        list_of_ret = []
        while cur_date <= pred_date:
            pred = self.predict(cur_date.strftime('%d.%m.%Y'))
            cur_date = cur_date + datetime.timedelta(days=1)

            list_of_ret.append(pred)

        return list_of_ret
