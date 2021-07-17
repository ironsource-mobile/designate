# Designate

**Designate** is a GitHub Action, intended for fetching application metadata from service registry, building corresponding Helm values and triggering Spinnaker pipelines.

## Usage

To deploy with Designate, use it in your GitHub Actions workflow:

```yaml
      - name: Designate
        uses: ironsource-mobile/designate@main
        with:
          name: example
          version: v0.1.0
          environment: dev
          pipeline: rollout
          chart: helm-chart-repo/example
```

This will fetch service metadata from the [service registry](https://github.com/ironsource-mobile/service-registry), render Helm values, find the matching environment by tags, and trigger Spinnaker deployment pipeline.

## Reference

### Concepts

**App** is a service, job, or any other workload entity in your ecosystem.

**Environment** is specifically a Kubernetes cluster, defined by the kind of environment it represents as well as a set of tags, describing its purpose. Environment definitions also contain important metadata, such as Spinnaker URL and cluster base domain.

**Deployment** is a process of deploying an app to a matching environment. Deployments are represented by environment kind, app version, Helm chart pointer, and the kind of deployment pipeline.

**Template** entity is a Jinja2-powered template of the app's Helm values file.

### GitHub Action inputs

- **name** — service name
- **environment** — deployment environment (i.e. dev, staging, prod)
- **pipeline** — pipeline name, default is `rollout`
- **chart** — name of app's Helm chart, omit to use the base chart
- **registry_repo** *(optional)* — name of Service Registry repo, default: `ironsource-mobile/service-registry`
- **registry_branch** *(optional)* — which branch to fetch from Service Registry repo, default is `main`
- **github_token** — since Service Registry is a private repo, this is a GitHub API key for accessing that repo

*Hint:* use GitHub Actions Secrets for storing `github_token`, to avoid disclosing it in your code

### Registry entry syntax

**Application**:

```yaml
kind: app

# `name` represents the service name
# Remember to keep it consistent to avoid deployment issues
name: foo-app

# `template` is the name of values template to use (see template section)
template: foo

# `tags` is a map of key-value pairs
# Deployment environment is selected based on the tags
tags:
  region: us-east-1
  owner: general
  team: developers
  project: demo
```

**Environment**:

```yaml
kind: environment

# This is the display name of the environment, however it is available in templates
name: general-dev

# Kind of environment: dev, staging, prod
# This is also used to match the deployment environment, provided to the GitHub Action
environment: dev

# Tags work as environment selectors: whichever environment has the same tags as the app,
# will be the one that app is deployed on (considering the `environment` value)
tags:
  region: us-east-1
  owner: general

# Environment metadata: base domain and Spinnaker API URL
domain: general-dev.us-east-1.example.com
spinnaker_url: https://spinnaker-api.general-dev.us-east-1.example.com
```

**Template**:

```yaml
kind: template

# `name` should match the `template` field in app definition
name: foo

# `template` is a string, containing Jinja2 template
# See below for available variables
template: |
  base-app:
    environment: {{ deployment.environment }}
    appName: {{ app.name }}
    project: {{ app.tags.project }}
    owner: {{ app.tags.owner }}
    team: {{ app.tags.team }}
    image:
      tag: {{ deployment.version }}
```

Available Jinja variables:

- `app` — app metadata:
  - `app.name`
  - `app.tags`
- `environment` — environment metadata:
  - `environment.tags`
  - `environment.domain`
- `deployment` — inputs provided to the Action:
  - `deployment.version`
  - `deployment.environment`
  - `deployment.pipeline`
  - `deployment.chart`

### Spinnaker webhook

Designate triggers Spinnaker pipeline, and passes rendered values as well as deployment parameters to Spinnaker as its payload:

```json
{
    "artifacts": [
        {
            "type": "embedded/base64",
            "reference": "BASE_64_ENCODED_RENDERED_VALUES",
            "name": "registry-values",
        }
    ],
    "parameters": {
        "version": "v1.2.3",
        "environment": "prod",
        "pipeline": "rollout",
        "chart": "helm-chart-repo/example"
    }
}
```

You can access Helm values as `registry-values` artifact of type *embedded/base64*, and all deployment parameters as Spinnaker parameters (e.g. `${ parameters.version }`).

## Development

Before starting, please read [Contributing guidelines](https://github.com/ironsource-mobile/designate/blob/main/CONTRIBUTING.md).

*Note:* This repo uses *main* as a default branch. Make sure you don't use *master* accidentally.

### How does it work?

A usual execution flow is following:

0. *GitHub Actions workflow is triggered*
1. GitHub Actions builds *Designate* image, and runs it with the passed parameters
2. *Designate* loads and parses entries from Service Registry repo
3. Filters app entries by name and picks the matching one
4. Matches `environment` input + app tags against environment entries and picks the matching env
5. Renders Helm values from the template
6. Triggers Spinnaker on the chosen cluster, providing rendered Helm values as an artifact

### Source code structure

Source code can be found under `designate` directory:

- **`deployment`** — deployment-related logic
- **`errors`** — error handling
- **`registry`** — registry interactions
- **`cli.py`** — main program, definition of CLI commands

GitHub Actions definition is in **`actions.yaml`**.

### Standards

Designate code shall follow OOP patterns. You can learn more [here](https://realpython.com/python3-object-oriented-programming/). Code style shall be [Black](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html). Code shall be formatted using Black formatter, [isort](https://pycqa.github.io/isort/) and linted with [flake8](https://flake8.pycqa.org/en/latest/#).
All dependencies shall be managed using [Poetry](https://python-poetry.org/docs).
Designate releases shall strictly follow [Semantic Versioning](https://semver.org) scheme.

### Prerequisites

To work on this project you need:

- Python 3.8+ (using [pyenv](https://github.com/pyenv/pyenv#installation) is heavily recommended)
- [Poetry](https://python-poetry.org/docs/#installation)
- IDE with [Black](https://github.com/psf/black#installation-and-usage) formatter, [flake8](https://flake8.pycqa.org/en/latest/#installation) linter and [isort](https://pycqa.github.io/isort/#installing-isort) tool installed

### Using Poetry

This project uses Poetry as a dependency management tool. It has a lot of advantages before plain pip, for example:

- automatic virtual env management
- better dependency management
- build system
- integration with test frameworks

Here are some example actions you should know:

```bash
# Activate the virtual environment and get a shell inside
poetry shell

# Install the app with all dependencies
poetry install

# Add a new dependency (identical to pip install x when not using Poetry)
poetry add x

# Remove a dependency
poetry remove x

# Bump package version (level is one of patch, minor, major)
poetry version level

# Run a command in the virtual environment
poetry run x

# Update dependencies
poetry update
```

All dependencies should be added using Poetry: `poetry add x`. Please try to reuse existing dependencies to avoid bloating the package; you can find the list of these in `pyproject.toml` or by running `poetry show`.

### Releases

**Designate** follows [semantic versioning](https://semver.org) guidelines. Version numbers don't include *v* prefix *unless* it is a tag name (i.e., tags look like `v1.2.3`, everything else — `1.2.3`).

All changes are kept track of in the changelog, which can be found in *CHANGELOG.md* file. This file follows *[keep-a-changelog](https://keepachangelog.com/en/1.0.0/)* format. Please make yourself familiar with it before contributing.

Generally, you should test your changes before creating a release. After that, create a *release candidate* pre-release, using the instruction below. Version number should be `1.2.3-rc.1` — an upcoming release version number with RC suffix. After extensively testing the release candidate, you can proceed to creating a release.

#### Release process

0. Checkout *main* branch.
1. Run `poetry version minor` (or `major` or `patch`, depending on severity of changes in the release). This will bump project version in `pyproject.toml`.
2. Change `[Unreleased]` H2 header in *CHANGELOG.md* to the new release version (e.g., `[1.2.3]`).
3. Add current date in ISO format (`YYYY-DD-MM`) after the header (e.g., `[1.2.3] - 2011-12-13`).
4. Add new `[Unreleased]` H2 header above all version headers.
5. Add compare link at the bottom of *CHANGELOG.md* as follows:
`[1.2.3]: https://github.com/ironsource-mobile/designate/compare/v1.2.2...v1.2.3` right below `[unreleased]` link (replace `1.2.3` with the new release version, `1.2.2` with the previous release version).
6. Change version in `[unreleased]` link at the bottom of *CHANGELOG.md* to the new release version (e.g., `[unreleased]: https://github.com/ironsource-mobile/designate/compare/v1.2.3...HEAD`).
7. Commit the changes to *main* branch. Commit message should be `Release v1.2.3`.
8. Create a release tag: `git tag v1.2.3`. This should be a *lightweight* tag, not an annotated one.
9. Push the changes and tag to GitHub: `git push && git push --tags`.

If you find the above instructions unclear, take a look at previous releases or contact project maintainers.
