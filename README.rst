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

    docker-compose -f service.yml pull
    docker-compose -f service.yml up -d --force-recreate
