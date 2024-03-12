import os
import os.path
import json
import tarfile
import shutil
from secrets import token_urlsafe

import yaml
import falcon
import falcon.asgi

from .config import ConfigSingleton
from .package import PackageManager
from .web import WebResource, PackageCacheEntry

class PublishResource:
    # A list of nonces we are currently using
    active_nonces = []

    @staticmethod
    def upload_url(nonce, token):
        return "%s/api/packages/versions/new/upload/%s/%s" % (ConfigSingleton.outside_url,
                                                              nonce,
                                                              token)

    @staticmethod
    def get_token_from_authorized(header):
        prep = header.strip()
        if (prep.startswith("Bearer")):
            return prep.split(" ")[-1].strip()
        elif not ConfigSingleton.check_authorization:
            return ""

        raise Exception("Unknown Authorization header: " + prep)

    async def on_get(self, req, resp):
        auth_header = req.headers.get("authorization", "")
        try:
            token = PublishResource.get_token_from_authorized(auth_header)
        except Exception:
            # Only treat this as unauthorized if we are checking authorization
            if ConfigSingleton.check_authorization:
                resp.content_type = "application/vnd.pub.v2+json"
                resp.status = falcon.HTTP_403
                resp.set_header("WWW-Authenticate", "Bearer realm=\"pub\", message=\"Unknown authentication header\"")
                return
            
        if (ConfigSingleton.check_authorization
            and token not in ConfigSingleton.allowed_tokens):
            resp.content_type = "application/vnd.pub.v2+json"
            resp.status = falcon.HTTP_403
            resp.set_header("WWW-Authenticate", "Bearer realm=\"pub\", message=\"Invalid authentication token\"")
            return

        nonce = token_urlsafe(64)
        upload_url = PublishResource.upload_url(nonce, token)
        PublishResource.active_nonces.append(nonce)

        resp.content_type = "application/vnd.pub.v2+json"
        resp.status = falcon.HTTP_200
        resp.text = json.dumps({
            "url": upload_url,
            "fields": {}
        })

class UploadResource:
    @staticmethod
    def finalize_url(nonce, token):
        return "%s/api/packages/versions/new/finalize/%s/%s" % (ConfigSingleton.outside_url,
                                                                nonce,
                                                                token)

    async def on_post(self, req, resp, nonce, auth):
        if not nonce in PublishResource.active_nonces:
            resp.status = falcon.HTTP_401
            return

        PublishResource.active_nonces.remove(nonce)
        form = await req.get_media()
        async for part in form:
            if part.content_type == "application/octet-stream":
                # TODO: What if the file already exists
                with open(os.path.join(ConfigSingleton.upload_dir, nonce), "ab") as f:
                    async for chunk in part.stream:
                        f.write(chunk)

        resp.status = falcon.HTTP_204
        resp.set_header("Location", UploadResource.finalize_url(nonce, auth))

class FinalizeResource:
    def unpack_pubspec(self, path):
        """
        Unpacks the pubspec.yaml from the tarball. Returns the path to the unpacked
        pubspec.yaml and to the folder it is unpacked into.
        """
        unpacked_path = path + "_unpacked"
        tar = tarfile.open(path)
        tar.extract("pubspec.yaml", unpacked_path)
        tar.close()

        return (os.path.join(unpacked_path, "pubspec.yaml"), unpacked_path)

    def cleanup(self, unpacked_path, path="", remove_archive=False):
        # Remove the unpacked version
        shutil.rmtree(unpacked_path)

        # Remove the archive, if specified
        if remove_archive:
            os.remove(path)

    async def on_get(self, req, resp, nonce, auth):
        path = os.path.join(ConfigSingleton.upload_dir, nonce)
        if not (os.path.exists(path) and os.path.isfile(path)):
            resp.status = falcon.HTTP_400
            resp.content_type = falcon.MEDIA_JSON
            resp.text = json.dumps({
                "error": {
                    "code": "0",
                    "message": "That file does not exist"
                }
            })
            return

        pubspec_path, unpacked_path = self.unpack_pubspec(path)
        with open(pubspec_path, "r") as f:
            pubspec = yaml.safe_load(f.read())
        name = pubspec["name"]

        if (ConfigSingleton.check_authorization
            and not name in ConfigSingleton.allowed_tokens[auth] and not 'any' in ConfigSingleton.allowed_tokens[auth]):
            resp.status = falcon.HTTP_403
            resp.content_type = falcon.MEDIA_JSON
            resp.text = json.dumps({
                "error": {
                    "code": "1",
                    "message": "You're not allowed to update this package"
                }
            })
            self.cleanup(unpacked_path, path, remove_archive=True)
            return

        result = PackageManager.update_package(name, pubspec)
        if not result:
            resp.status = falcon.HTTP_304
            resp.content_type = falcon.MEDIA_JSON
            resp.text = json.dumps({
                "error": {
                    "code": 3,
                    "message": "That version is already published"
                }
            })
            self.cleanup(unpacked_path, path, remove_archive=True)
            return

        # Notify the Web view of the new or changed package
        WebResource.data_cache[result[0]] = PackageCacheEntry(
            result[0],
            result[1],
            result[2],
            result[3],
            result[4]
        )
        
        # Store the archive
        versions_path = PackageManager.package_versions_path(name)
        if not (os.path.exists(versions_path) and os.path.isdir(versions_path)):
            # Create the versions directory if needed
            os.mkdir(versions_path)

        shutil.move(path, os.path.join(versions_path, pubspec["version"] + ".tar.gz"))

        self.cleanup(unpacked_path)

        resp.status = falcon.HTTP_200
        resp.content_type = "application/vnd.pub.v2+json"
        resp.text = json.dumps({
            "success": {
                "message": "Published"
            }
        })

class ArchiveResource:
    async def on_get(self, req, resp, package, version):
        path = os.path.join(PackageManager.package_path(package), "versions", version + ".tar.gz")
        if not (os.path.exists(path) and os.path.isfile(path)):
            resp.status = falcon.HTTP_404
            return

        resp.content_type = "application/octet-stream"
        with open(path, "rb") as f:
            resp.data = f.read()
        resp.status = falcon.HTTP_200

class PackageResource:
    @staticmethod
    def archive_url(package, version):
        return "%s/archive/%s/%s" % (ConfigSingleton.outside_url,
                                     package,
                                     version)

    async def on_get(self, req, resp, package):
        if not PackageManager.package_exists(package):
            resp.status = falcon.HTTP_404
            return

        with open(os.path.join(PackageManager.package_path(package), "info.json"), "r") as f:
            data = json.loads(f.read())

        data["latest"]["archive_url"] = PackageResource.archive_url(package,
                                                                    data["latest"]["version"])

        for i in range(len(data["versions"])):
            version = data["versions"][i]["version"]
            data["versions"][i]["archive_url"] = PackageResource.archive_url(package,
                                                                             version)

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.text = json.dumps(data)

# Load the configuration
ConfigSingleton.load_config()

# Start the app
app = falcon.asgi.App()
app.add_route("/api/packages/versions/new", PublishResource())
app.add_route("/api/packages/{package}", PackageResource())
app.add_route("/api/packages/versions/new/upload/{nonce}/{auth}", UploadResource())
app.add_route("/api/packages/versions/new/finalize/{nonce}/{auth}", FinalizeResource())
app.add_route("/archive/{package}/{version}", ArchiveResource())
app.add_route("/", WebResource())
