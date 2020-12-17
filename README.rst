##############################
Modeling of COVID-19 spreading
##############################

|colab| |build| |deploy| 

.. |colab| image:: https://colab.research.google.com/assets/colab-badge.svg
    :target: https://colab.research.google.com/github/vova98/covidModeling/blob/main/experiment/experiment.ipynb
    :alt: colab

.. |build| image:: https://github.com/vova98/covidModeling/workflows/Testing%20Compatibility/badge.svg
    :target: https://github.com/vova98/covidModeling/actions
    :alt: Build
    
.. |deploy| image:: https://github.com/vova98/covidModeling/workflows/Publish%20Docker%20image/badge.svg
    :target: https://github.com/vova98/covidModeling/actions
    :alt: Deploy

Description
===========

Данные по заболеваемости в регионах Российской Федерации взяты с `сайта <https://стопкоронавирус.рф/information/>`_.

Готовый сервис доступен по `адресу <http://54.237.200.39>`_.

Requirements
============

.. code-block:: bash

    docker-compose version 1.27.4, build 40524192
    
Run By Docker
=============

.. code-block:: bash

    sudo -E docker-compose pull
    sudo -E docker-compose up -d --force-recreate

Build From Source
=================

.. code-block:: bash

    sudo -E docker-compose build
    sudo -E docker-compose up -d --force-recreate
