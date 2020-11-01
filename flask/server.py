# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
from datetime import timedelta

from flask import render_template, Flask, request, Response

from api import (approximate, get_cities, get_data_field, get_models, get_dates,
                 update_data, LoggerSinglton, get_stats)


app = Flask(__name__)

LoggerSinglton.init()

@app.route('/')
@app.route('/main')
def main():
    LoggerSinglton.init()
    logging.debug('new connection')

    models = get_models(with_approximator=False)
    cities = get_cities()
    fields = get_data_field()
    dates = get_dates(list(cities.keys())[0])
    dates = dates + ((datetime.strptime(
        dates[1], '%d.%m.%Y') + timedelta(days=1)).strftime('%d.%m.%Y'),)

    return render_template(
        'main.html',
        cities=cities,
        models=models,
        fields=fields,
        default_city=list(cities.keys())[0],
        default_dates={
            'use_date_from': dates[0],
            'use_date_to': dates[1],
            'predict_date_to': dates[2],
        })

@app.route('/stats')
def stats():
    return Response(get_stats(), mimetype='application/json')


@app.route('/update', methods=['GET'])
def update():
    last_date = update_data()
    return Response({'last_date': last_date}, mimetype='application/json')


@app.route('/json/<city>', methods=['GET'])
def get_json(city):

    models = request.args.get('models')
    if models:
        models_all = json.loads(models)
        models = dict()
        for key in models_all:
            if models_all[key]['use'] == 1:
                models[key] = dict()
                models[key]['parameters'] = models_all[key]['parameters']
    else:
        models = dict()

    fields = request.args.get('fields')
    if fields:
        fields_all = json.loads(fields)
        fields = []
        for key in fields_all:
            if fields_all[key] == 1:
                fields.append(key)
    else:
        fields = []

    date = request.args.get('date')
    if date:
        date = json.loads(date)
    else:
        date = None

    approx = approximate(city, json.dumps(models), json.dumps(date))

    return Response(json.dumps(approx), mimetype='application/json')
