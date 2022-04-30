import os
import os.path
import json

from .config import ConfigSingleton

class PackageManager:
    @staticmethod
    def package_path(name):
        """
        Returns the path to the package with name @name. Does not imply its existence.
        """
        return os.path.join(ConfigSingleton.package_dir, name)

    @staticmethod
    def package_exists(name):
        """
        Return true if the package exists in the system. False otherwise.
        """
        path = PackageManager.package_path(name)
        return os.path.exists(path) and os.path.isdir(path)

    @staticmethod
    def package_info_path(name):
        """
        Return the path to the packages info.json metadata file. Does not imply its
        existence.
        """
        return os.path.join(PackageManager.package_path(name), "info.json")

    @staticmethod
    def package_versions_path(name):
        """
        Return the path to the packages versions directory. Does not imply its
        existence.
        """
        return os.path.join(PackageManager.package_path(name), "versions")

    @staticmethod
    def update_package(name, pubspec_data):
        """
        Update the package's metadata. Returns a tuple of metadata if everything went well.
        None, if the version is already added.
        """
        info = {}
        package_exists = PackageManager.package_exists(name)
        if not package_exists:
            info = {
                "name": pubspec_data["name"],
                "latest": {},
                "versions": []
            }
        else:
            with open(PackageManager.package_info_path(name), "r") as f:
                info = json.loads(f.read())

        versions = [ v["version"] for v in info["versions"] ]
        if pubspec_data["version"] in versions:
            return None

        if not package_exists:
            os.mkdir(PackageManager.package_path(name))
            os.mkdir(PackageManager.package_versions_path(name))

        version = {
            "version": pubspec_data["version"],
            "pubspec": pubspec_data
        }
        info["latest"] = version
        info["versions"].append(version) 
        
        with open(PackageManager.package_info_path(name), "w") as f:
            f.write(json.dumps(info))

        return (
            info["name"],
            version,
            "", # TODO
            pubspec_data.get("description", ""),
            pubspec_data.get("homepage", "")
        )
