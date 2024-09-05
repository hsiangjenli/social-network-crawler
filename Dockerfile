FROM sphinxdoc/sphinx:8.0.0

WORKDIR /workspace

RUN apt-get update && apt-get install -y graphviz gcc libgraphviz-dev python3-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir sphinx_rtd_theme pygraphviz autodoc_pydantic[erdantic] pytest-playwright && playwright install