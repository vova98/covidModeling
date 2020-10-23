# -*- coding: utf-8 -*-
import base64
from io import BytesIO
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import render_template, Flask, request, Response

from api import approximate, get_cities, get_data_field, get_models


app = Flask(__name__)


@app.route('/')
@app.route('/main')
def main():
    models = get_models(with_approximator=False)
    cities = get_cities()
    fields = get_data_field()
    return render_template(
        'main.html',
        cities=cities,
        models=models,
        fields=fields,
        default_city=list(cities.keys())[0])

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

    approx = approximate(city, json.dumps(models), date)

    return Response(json.dumps(approx), mimetype='application/json')