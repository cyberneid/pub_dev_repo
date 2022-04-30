from dataclasses import dataclass
import os
import os.path
import json

import falcon
import jinja2

from .config import ConfigSingleton
from .package import PackageManager

index_template = jinja2.Template(source="""
<html>
  <head>
    <title>Pub Repository</title>
  </head>
  <body>
    <h1>Pub Repository</h1>
    <div style="display: flex; flex-direction: column;">
      {% for package in packages %}
      <div>
        <h2><a href="{{ package.homepage|e }}">{{ package.name|e }}</a></h2>

        <p>{{ package.description|e }}</p>

        <p>Latest version: {{ package.latest_version|e }} (unknown ago)</p>
      </div>
      <hr />
      {% endfor %}
    </div>
  </body>
</html>
""")

@dataclass
class PackageCacheEntry:
    name: str
    latest_version: str
    published: str
    description: str
    homepage: str

class WebResource:
    # package name -> PackageCacheEntry
    data_cache = {}
    data_loaded = False

    @staticmethod
    def load_package_metadata():
        # Make sure that we don't have data here that is outdated
        WebResource.data_cache = {}
        
        base_path = PackageManager.package_path("")
        for item in os.listdir(base_path):
            package_path = os.path.join(base_path, item)
            if not os.path.isdir(package_path):
                continue

            info_path = PackageManager.package_info_path(item)
            if not os.path.exists(info_path):
                WebResource.data_cache[item] = PackageCacheEntry(
                    item,
                    "?",
                    "", # TODO
                    "?",
                    "?"
                )
                continue

            with open(info_path, "r") as f:
                data = json.loads(f.read())

            if "latest" not in data:
                WebResource.data_cache[item] = PackageCacheEntry(
                    item,
                    "N/A",
                    "", # TODO
                    "",
                    ""
                )
                continue
                
            WebResource.data_cache[item] = PackageCacheEntry(
                item,
                data["latest"]["version"],
                "", # TODO
                data["latest"].get("description", ""),
                data["latest"].get("homepage", "#")
            )
        WebResource.data_loaded = True

    async def on_get(self, req, resp):
        if not WebResource.data_loaded:
            WebResource.load_package_metadata()

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_HTML
        resp.text = index_template.render(packages=WebResource.data_cache.values())
