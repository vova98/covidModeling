from scipy.interpolate import interp1d
import datetime

class Approximator(object):
    r"""Базовый класс для всех аппроксимирующих моделей."""
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
        
        :return: список словарей вида: {'date': строка в формате day.month.year,
                                        'sick': int, 
                                        'recovered': int,
                                        'died': int}
        :rtype: list
        """
        raise NotImplementedError

class SplineApproximator(object):
    r"""
    Простая реализация аппроксиматора на основе сплайнов.
    """
    def __init__(self):
        super(SplineApproximator, self).__init__()
        
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
            x = [p for p in points]
            self.approximators[model] = interp1d(x, y, kind='cubic',
                                                 fill_value="extrapolate")
            
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
        _id = self.last_fited_element[0] \
              + (pred_date - self.last_fited_element[1]).days
        
        ret = dict()
        ret['date'] = date
        for key in self.approximators:
            ret[key] = self.approximators[key](_id)
        
        return ret

    def predict_to(self, date):
        r"""
        Данная функция должна возвращать предсказания для всех дат начиная с 
            последней доступной в обучении и до заданой.
        Предсказывать нужно количество заболевших, выздоровших и умерших.

        :param date: Строка формата "day.month.year"
        :type date: str 
        
        :return: список словарей вида: {'date': строка в формате day.month.year,
                                        'sick': int, 
                                        'recovered': int,
                                        'died': int}
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







