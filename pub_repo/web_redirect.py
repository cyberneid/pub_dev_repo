from dataclasses import dataclass
import os
import os.path
import json
from datetime import datetime

import falcon
import jinja2

from .config import ConfigSingleton
from .package import PackageManager

index_template = jinja2.Template(source="""
<html>
  <head>
    <title>{{ title|e }}</title>
  </head>
  <body>
    <h1>{{ title|e }}</h1>
    <div style="display: flex; flex-direction: column;">
      {% for package in packages %}
      <div>
        <h2><a href="{{ package.homepage|e }}">{{ package.name|e }}</a></h2>

        <p>{{ package.description|e }}</p>

        <p>Latest version: {{ package.latest_version|e }} ({{ timedeltas[package.name]|e }})</p>
      </div>
      <hr />
      {% endfor %}
    </div>
  </body>
</html>
""")




class WebResourceRedirect:

    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_302
        resp.location = "https://www.cyberneid.com"
