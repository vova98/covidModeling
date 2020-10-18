# -*- coding: utf-8 -*- 
from flask import render_template, Flask, request, jsonify, Response

from threading import Thread

import tempfile
import time
import json
import re
import os

from time import gmtime, strftime

import pandas as pd
import numpy as np

app = Flask(__name__)

@app.route('/')
@app.route('/main')
def check():
    return render_template('main.html')
