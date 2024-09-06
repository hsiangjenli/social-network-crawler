.. social-network-crawler documentation master file, created by
   sphinx-quickstart on Mon Sep  2 01:01:00 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to social-network-crawler's documentation!
==================================================

How to install
--------------

#. Install the package via pip
#. Install the required browsers via playwright

.. code-block:: bash

   pip install git+https://github.com/hsiangjenli/social-network-crawler.git
   playwright install # optional, if you want to use playwright


.. toctree::
   :glob:
   :caption: Base Model
   :maxdepth: 1

   base_model

.. toctree::
   :glob:
   :caption: Crawler
   :maxdepth: 1

   crawler