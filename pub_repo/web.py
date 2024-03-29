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

@dataclass
class PackageCacheEntry:
    name: str
    latest_version: str
    last_published: str
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
                    -1,
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
                    data.get("last_published", -1),
                    "",
                    ""
                )
                continue
            
            WebResource.data_cache[item] = PackageCacheEntry(
                item,
                data["latest"]["version"],
                data.get("last_published", -1),
                data["latest"]["pubspec"].get("description", ""),
                data["latest"]["pubspec"].get("homepage", "#")
            )
        WebResource.data_loaded = True

    async def on_get(self, req, resp):
        if not WebResource.data_loaded:
            WebResource.load_package_metadata()

        timedeltas = {}
        now = datetime.now()
        packages = WebResource.data_cache.values()
        print(packages)
        #packages.sort(key="title")
        for package in packages:
            if package.last_published > -1:
                delta = now - datetime.fromtimestamp(package.last_published)
                delta_str = ""
                
                if hasattr(delta, "weeks"):
                    weeks = delta.weeks
                    if weeks >= 4:
                        delta_str = str(divmod(weeks, 4)[0]) + " months ago"
                    else:
                        delta_str = str(delta.weeks) + " weeks ago"
                elif hasattr(delta, "hours"):
                    hours = delta.hours
                    if hours >= 24:
                        delta_str = str(divmod(hours, 24)[0]) + " + days ago"
                    else:
                        delta_str = str(hours) + " hours ago"
                else:
                    delta_str = "Just now"

                timedeltas[package.name] = delta_str

            else:
                if package.latest_version not in ("", "N/A"):
                    timedeltas[package.name] = "N/A"
                else:
                    timedeltas[package.name] = "not published"
            
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_HTML
        resp.text = index_template.render(packages=packages,
                                          timedeltas=timedeltas,
                                          title=ConfigSingleton.web_title)
