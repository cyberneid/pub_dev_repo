# pub_repo

A simple selfhostable pub repository with support for publishing.

## Usage

Install using `setup.py install` and run with any ASGI host, like for example
`daphne`: `daphne -p 8000 pub_repo.repo_asgi:app`.
sudo daphne -b 0.0.0.0 -p 8000 pub_repo.repo_asgi:app

## Configuration

pub_repo reads its configuration either from `./pub_repo.yaml` or from the path specified
by the `PUB_REPO_CONFIG` environment variable.

```yaml
# Path to where packages are stored
package_dir: /var/lib/pubrepo/packages

# Path to where uploads are tempoarily stored
upload_dir: ./uploads

# URL on which the service can be reached
outside_url: http://127.0.0.1:8000

# Whether to check authorization for publishing and finalizing.
# Note that this means that EVERYONE CAN PUBLISH on ANY PACKAGE and
# UPLOAD ANY PACKAGE. Use with care.
check_authorization: false

# The title of the web view
web_title: Some Repository

# Authorization tokens that are allowed to publish. These tokens must be URL safe and not
# contain slashes.
tokens:
  abc123:
    # List of packages that this token can publish on
    - package_a
  some_other_token:
    - package_b
    - package_a

```

## License

See `LICENSE`.
