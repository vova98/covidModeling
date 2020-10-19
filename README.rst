##############################
Modeling of COVID-19 spreading
##############################

|build| |deploy| 

.. |build| image:: https://github.com/vova98/covidModeling/workflows/Testing%20Compatibility/badge.svg
    :target: https://github.com/vova98/covidModeling/actions
    :alt: Build
    
.. |deploy| image:: https://github.com/vova98/covidModeling/workflows/Publish%20Docker%20image/badge.svg
    :target: https://github.com/vova98/covidModeling/actions
    :alt: Deploy
    
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
