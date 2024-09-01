FROM sphinxdoc/sphinx:8.0.0

WORKDIR /workspace

RUN pip3 install sphinx_rtd_theme