===========================
pyBIVAS
===========================

.. image:: https://api.travis-ci.com/jurjendejong/pyBIVAS.svg
        :target: https://travis-ci.com/jurjendejong/pyBIVAS
        :alt: Build status

.. image:: https://readthedocs.org/projects/pybivas/badge/?version=latest
        :target: https://pybivas.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

This module provides various scripts to work with the software BIVAS by Charta Software (and Rijkswaterstaat). This software is used for network analyses of inland shipping. The module contains functions for specific queries to the BIVAS SQL-database and an API to modify and run simulations. 

Most routines have been developed as part of the programs Deltaprogramma Zoet Water and in Klimaatbestendige Netwerken. 

* Free software: MIT license
* Documentation: https://pyBIVAS.readthedocs.io.


Features
--------

* API to BIVAS console through python
* Advanced SQL-queries
* Routines for running many scenario's

How to install
--------------

    pip install -e .

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
