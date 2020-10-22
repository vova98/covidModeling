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


@app.route('/graph/<city>', methods=['GET'])
def get_city_graph(city):
    width = int(request.args.get('width', 800))
    hight = int(request.args.get('hight', 600))

    if width < 800:
        width = 800
    if hight < 800:
        hight = 600

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

    ax = plt.figure(figsize=(width//100, hight//100)).gca()

    type_of_points = ['.', '+', '*', 'x', 'o', '^', '>', '<']*len(fields)
    type_of_lines = ['-', '--', '-.', '--.']*len(fields)

    colors = ['blue', 'red', 'green', 'orange', 'black']*len(fields)

    for f, field in enumerate(fields):
        for a, appr in enumerate(approx):
            keys = sorted(list(approx[appr].keys()))

            x = [key for key in keys]
            y = [approx[appr][key][field] for key in keys]
            x_labels = [approx[appr][key]['date'] for key in keys]

            if appr == 'real':
                ax.plot(x, y, type_of_points[f], label=appr + ' ' + field,
                        color=colors[a])
            else:
                ax.plot(x, y, type_of_lines[f], label=appr + ' ' + field,
                        color=colors[a])

            ax.set_xticks(x)
            ax.set_xticklabels(x_labels)

    ax.legend(loc='best')
    ax.grid()
    plt.setp(ax.get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    text = 'data:image/png;base64, {}'.format(plot_url)
    return Response(text, mimetype='text/plain')
