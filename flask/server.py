# -*- coding: utf-8 -*- 
from flask import render_template, Flask, request, jsonify, Response

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import tempfile
import json
import re

from io import BytesIO
import base64

import pandas as pd
import numpy as np

from api import get_cities, get_city_statistic, get_models, approximate

app = Flask(__name__)

@app.route('/')
@app.route('/main')
def main():
    models = get_models()
    cities = get_cities()
    return render_template(
        'main.html', 
        cities=cities, 
        models=models, 
        default_city=list(cities.keys())[0])


@app.route('/graph/<city>', methods=['GET'])
def get_city_graph(city):

    models = request.args.get('models')
    if models:
        models_all = json.loads(models)
        models = []
        for key in models_all:
            if models_all[key] == 1:
                models.append(key)
    else:
        models = []
    date = request.args.get('date')
    if date:
        date = json.loads(date)
    else:
        date = None

    data = get_city_statistic(city)

    approx = approximate(data, models, date)

    ax = plt.figure(figsize=(8.0, 4.0)).gca()
    for k in approx:
        keys = sorted(list(approx[k].keys()))

        x = [key for key in keys]
        y = [approx[k][key]['sick'] for key in keys]
        x_labels = [approx[k][key]['date'] for key in keys]
        

        if k == 'real':
            ax.plot(x, y, '.', label=k)
        else:
            ax.plot(x, y, '-', label=k)

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