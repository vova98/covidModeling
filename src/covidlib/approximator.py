# -*- coding: utf-8 -*-
from abc import ABC
from scipy.interpolate import interp1d
import datetime
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from statsmodels.tsa.arima.model import ARIMA


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
            x = [datetime.datetime.strptime(data[p]['date'],
                                            '%d.%m.%Y').timestamp() for p in
                 points]
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
            x = np.array(
                [datetime.datetime.strptime(data[p]['date'], '%d.%m.%Y'
                                            ).timestamp() for p in points]
            ).reshape([-1, 1])
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
    Реализация метода Нестерова, в случае фиксированых параметров \Delta и
    \gamma
    """
    _name = 'Нестеров с постоянными параметрами'
    _parameters = {'gamma': {
        'description': 'Ежедневная скорость заражения'
                       ' В диапазоне от 0. до 10.',
        'type': 'continues',
        'values': [],
        'default': '0.075',
        'min': '0.0',
        'max': '10.0'},
        'k': {
            'description': 'Ежедневная смертность'
                           ' В диапазоне от 0. до 10.',
            'type': 'continues',
            'values': [],
            'default': '0.0007',
            'min': '0.0',
            'max': '10.0'},
        'l': {
            'description': 'Ежедневная скорость выздоровления'
                           ' В диапазоне от 0. до 10.',
            'type': 'continues',
            'values': [],
            'default': '0.03',
            'min': '0.0',
            'max': '10.0'},
        'delta': {
            'description': 'Параметр задержки заболевения.'
                           ' В диапазоне от 1 до 30',
            'type': 'continues',
            'values': [],
            'default': '14',
            'min': '1',
            'max': '30'}}

    def __init__(self, gamma=1.0, k=0.0007, l=0.03, delta=10):
        super(NesterovConstantGamma, self).__init__()

        self.gamma = float(gamma)
        if self.gamma < float(self._parameters['gamma']['min']):
            self.gamma = float(self._parameters['gamma']['min'])
        if self.gamma > float(self._parameters['gamma']['max']):
            self.gamma = float(self._parameters['gamma']['max'])

        self.k = float(k)
        if self.k < float(self._parameters['k']['min']):
            self.k = float(self._parameters['k']['min'])
        if self.k > float(self._parameters['k']['max']):
            self.k = float(self._parameters['k']['max'])

        self.l = float(l)
        if self.l < float(self._parameters['l']['min']):
            self.l = float(self._parameters['l']['min'])
        if self.l > float(self._parameters['l']['max']):
            self.l = float(self._parameters['l']['max'])

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
            date = datetime.datetime.strptime(data[key]['date'],
                                              '%d.%m.%Y').date()
            if date not in self.dict_of_data:
                self.dict_of_data[date] = dict()
            self.dict_of_data[date]['new sick'] = data[key]['sick']
            self.dict_of_data[date]['new died'] = data[key]['died']
            self.dict_of_data[date]['new reco'] = data[key]['recovered']

        # Надобы обработать пропуск значений

        for key in self.dict_of_data:
            self.dict_of_data[key]['sick'] = (self.dict_of_data.get(
                key - datetime.timedelta(days=1), {'sick': 0})['sick']
                + self.dict_of_data[key]['new sick'])

            self.dict_of_data[key]['S'] = self.dict_of_data.get(
                key + datetime.timedelta(days=-1), {'S': 0})['S'] \
                + self.dict_of_data[key]['new sick'] \
                - self.dict_of_data[key]['new died'] \
                - self.dict_of_data[key]['new reco'] \

        for key in self.dict_of_data:
            self.dict_of_data[key]['gamma'] = self.gamma
            self.dict_of_data[key]['k'] = self.k
            self.dict_of_data[key]['l'] = self.l
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
            self.dict_of_data[cur_date]['k'] = self.k
            self.dict_of_data[cur_date]['l'] = self.l
            self.dict_of_data[cur_date]['delta'] = self.delta

            # C(d) = gamma(d - \delta) * (T(d - 1) - T(d - \delta - 1))
            self.dict_of_data[cur_date]['new sick'] = int(
                self.dict_of_data.get(
                    cur_date - datetime.timedelta(
                        days=self.dict_of_data[cur_date]['delta']),
                    {'gamma': self.gamma})['gamma']
                * (self.dict_of_data.get(cur_date - datetime.timedelta(days=1),
                                         {'sick': 0})['sick']
                   - self.dict_of_data.get(cur_date - datetime.timedelta(
                       days=self.dict_of_data[cur_date]['delta'] + 1),
                       {'sick': 0})['sick']
                   )
            )

            self.dict_of_data[cur_date]['sick'] = self.dict_of_data.get(
                cur_date - datetime.timedelta(days=1),
                {'sick': 0})['sick'] + self.dict_of_data[cur_date]['new sick']
            self.dict_of_data[cur_date]['new died'] = int(
                self.dict_of_data.get(cur_date, {'k', self.k})['k'] \
                * self.dict_of_data[cur_date + datetime.timedelta(days=-1)]['S']
            )
            self.dict_of_data[cur_date]['new reco'] = int(
                self.dict_of_data.get(cur_date, {'l', self.l})['l'] \
                * self.dict_of_data[cur_date + datetime.timedelta(days=-1)]['S']
            )
            self.dict_of_data[cur_date]['S'] = self.dict_of_data.get(
                cur_date + datetime.timedelta(days=-1), {'S': 0})['S'] \
                + self.dict_of_data[cur_date]['new sick'] \
                - self.dict_of_data[cur_date]['new died'] \
                - self.dict_of_data[cur_date]['new reco'] \


            cur_date = cur_date + datetime.timedelta(days=1)

        return {'date': date.strftime('%d.%m.%Y'),
                'sick': self.dict_of_data[date]['new sick'],
                'recovered': self.dict_of_data[date]['new died'],
                'died': self.dict_of_data[date]['new reco']}

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


class Nesterov(Approximator):
    r"""
    Реализация метода Нестерова, в случае фиксированого параметра \Delta
    и предсказаний \gamma, k и l
    """
    _name = 'Модель Нестерова'
    _parameters = {'model': {
        'description': 'Модель предсказания: ARIMA',
        'type': 'choise',
        'values': ['ARIMA'],
        'default': 'ARIMA',
        'min': None,
        'max': None},
        'delta': {
            'description': 'Параметр задержки заболевения.'
                           ' В диапазоне от 1 до 30',
            'type': 'continues',
            'values': [],
            'default': '14',
            'min': '1',
            'max': '30'}}

    def __init__(self, delta=14, model='ARIMA'):
        super(Nesterov, self).__init__()

        self.delta = int(delta)
        if self.delta < int(self._parameters['delta']['min']):
            self.delta = int(self._parameters['delta']['min'])
        if self.delta > int(self._parameters['delta']['max']):
            self.delta = int(self._parameters['delta']['max'])

        self.gamma = 1 / self.delta
        self.k_param = 0.0007
        self.l_param = 0.03

        self.model = model

    def calculate_S(self, date):
        # S(d) = S(d - 1) + C(d) - D(d) - L(d)
        return (self.dict_of_data.get(date + datetime.timedelta(days=-1),
                                      {'S': 0})['S']
                + self.dict_of_data[date]['new sick']
                - self.dict_of_data[date]['new died']
                - self.dict_of_data[date]['new reco'])

    def calculate_gamma(self, key):
        # gamma(d) = C(d + \delta) / (T(d + \delta - 1) - T(d - 1))
        delta = self.dict_of_data[key]['delta']
        return (self.dict_of_data[key + datetime.timedelta(days=delta)]
                ['new sick']
                / (self.dict_of_data[key + datetime.timedelta(days=delta - 1)]
                   ['sick'] - self.dict_of_data.get(
                   key + datetime.timedelta(days=-1), {'sick': 0})['sick'])
                )

    def calculate_k_and_l(self, key):
        # k(d) = D(d) / S(d - 1)
        # l(d) = R(d) / S(d - 1)
        def calc(value):
            return (value / S_prev) if S_prev != 0 else 0

        S_prev = self.dict_of_data.get(key + datetime.timedelta(days=-1),
                                       {'S': 0})['S']
        self.dict_of_data[key]['k'] = calc(self.dict_of_data[key]['new died'])
        self.dict_of_data[key]['l'] = calc(self.dict_of_data[key]['new reco'])

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
            date = datetime.datetime.strptime(data[key]['date'],
                                              '%d.%m.%Y').date()
            if date not in self.dict_of_data:
                self.dict_of_data[date] = dict()
            self.dict_of_data[date]['new sick'] = data[key]['sick']
            self.dict_of_data[date]['new died'] = data[key]['died']
            self.dict_of_data[date]['new reco'] = data[key]['recovered']

        # Надо бы обработать пропуск значений

        for key in self.dict_of_data:
            self.dict_of_data[key]['sick'] = (self.dict_of_data.get(
                key - datetime.timedelta(days=1), {'sick': 0})['sick']
                + self.dict_of_data[key]['new sick'])

        if self.model == 'ARIMA':
            for key in self.dict_of_data:
                self.dict_of_data[key]['delta'] = self.delta
                try:
                    self.dict_of_data[key]['gamma'] = self.calculate_gamma(key)
                except Exception:
                    pass

                self.dict_of_data[key]['S'] = self.calculate_S(key)
                self.calculate_k_and_l(key)

            gammas = [self.dict_of_data[key]['gamma'] for key in
                      self.dict_of_data if 'gamma' in self.dict_of_data[key]]
            g_dates = [key.strftime('%Y-%m-%d') for key in self.dict_of_data if
                       'gamma' in self.dict_of_data[key]]
            ds = [self.dict_of_data[key]['k'] for key in self.dict_of_data if
                  'k' in self.dict_of_data[key]]
            ls = [self.dict_of_data[key]['l'] for key in self.dict_of_data if
                  'l' in self.dict_of_data[key]]
            dl_dates = [key.strftime('%Y-%m-%d') for key in self.dict_of_data if
                        'k' in self.dict_of_data[key]]

            self.gamma_model = ARIMA(pd.Series(gammas, index=g_dates),
                                     order=(6, 0, 4), trend='n').fit()
            self.d_model = ARIMA(pd.Series(ds, index=dl_dates),
                                 order=(5, 1, 4), trend='n').fit()
            self.l_model = ARIMA(pd.Series(ls, index=dl_dates),
                                 order=(6, 1, 6), trend='n').fit()

            for key in self.dict_of_data:
                self.predict_params(key)

    def predict_params(self, date):
        date_str = date.strftime('%Y-%m-%d')
        if 'gamma' not in self.dict_of_data[date]:
            self.dict_of_data[date]['gamma'] = \
                self.gamma_model.predict(start=date_str,
                                         end=date_str).values[0]
        if 'k' not in self.dict_of_data[date]:
            self.dict_of_data[date]['k'] = \
                self.d_model.predict(start=date_str,
                                     end=date_str).values[0]
        if 'l' not in self.dict_of_data[date]:
            self.dict_of_data[date]['l'] = \
                self.l_model.predict(start=date_str,
                                     end=date_str).values[0]

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
            self.predict_params(cur_date)
            self.dict_of_data[cur_date]['delta'] = self.delta

            # gamma(d) = gamma(d - \delta) * (C(d - 1) - C(d - \delta + 1))
            self.dict_of_data[cur_date]['new sick'] = int(
                self.dict_of_data.get(
                    cur_date - datetime.timedelta(days=self.dict_of_data[
                        cur_date]['delta']),
                    {'gamma': self.gamma})['gamma'] * (self.dict_of_data.get(
                        cur_date - datetime.timedelta(days=1),
                        {'sick': 0})['sick'] - self.dict_of_data.get(
                        cur_date - datetime.timedelta(days=self.dict_of_data[
                            cur_date]['delta'] + 1),
                        {'sick': 0})['sick']))

            # D(d) = k(d) * S(d - 1)
            self.dict_of_data[cur_date]['new died'] = int(
                self.dict_of_data.get(cur_date, {'k', self.k_param})['k']
                * self.dict_of_data[cur_date + datetime.timedelta(days=-1)]['S']
            )
            # R(d) = l(d) * S(d - 1)
            self.dict_of_data[cur_date]['new reco'] = int(
                self.dict_of_data.get(cur_date, {'l', self.l_param})['l']
                * self.dict_of_data[cur_date + datetime.timedelta(days=-1)]['S']
            )
            self.dict_of_data[cur_date]['S'] = self.calculate_S(cur_date)

            self.dict_of_data[cur_date]['sick'] = self.dict_of_data.get(
                cur_date - datetime.timedelta(days=1),
                {'sick': 0})['sick'] + self.dict_of_data[cur_date]['new sick']

            cur_date = cur_date + datetime.timedelta(days=1)

        return {'date': date.strftime('%d.%m.%Y'),
                'sick': self.dict_of_data[date]['new sick'],
                'recovered': self.dict_of_data[date]['new reco'],
                'died': self.dict_of_data[date]['new died']}

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
