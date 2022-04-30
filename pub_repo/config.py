import os

import yaml

class ConfigSingleton:
    """
    Kind-of-singleton holding all the static service configuration.
    """
    # Where packages are stored
    package_dir: str
    # Where uploads are tempoarily are stored
    upload_dir: str
    # The external URL that this service is exposed on
    outside_url: str
    # The title to show in the web view. Defaults to "Pub Repository"
    web_title: str
    # Whether to check authorization when publishing
    check_authorization: bool
    # Mapping authorization token to list of packages that it can publish on
    allowed_tokens: dict

    @staticmethod
    def load_config():
        """
        Load the configuration into the singleton class.
        """
        path = os.environ.get("PUB_REPO_CONFIG", "./pub_repo.yaml")

        if not (os.path.exists(path) and os.path.isfile(path)):
            raise Exception("Config file not found at " + path)

        with open(path, "r") as f:
            data = yaml.safe_load(f.read())

        ConfigSingleton.package_dir = data["package_dir"]
        ConfigSingleton.upload_dir = data["upload_dir"]
        ConfigSingleton.outside_url = data["outside_url"]
        ConfigSingleton.web_title = data.get("web_title", "Pub Repository")
        ConfigSingleton.check_authorization = data["check_authorization"]
        ConfigSingleton.allowed_tokens = data["tokens"]
        
        if not ConfigSingleton.check_authorization:
            print("WARNING: NOT CHECKING TOKENS! EVERYONE CAN PUBLISH UPDATES FOR "
                  "EVERY PACKAGE AND PUBLISH ANY PACKAGE! DO NOT USE IN PRODUCTION")

        # Create directories if they don't exist
        if not os.path.exists(ConfigSingleton.package_dir):
            os.makedirs(ConfigSingleton.package_dir)
        if not os.path.exists(ConfigSingleton.upload_dir):
            os.makedirs(ConfigSingleton.upload_dir)
