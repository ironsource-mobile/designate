#!/usr/bin/env python3
import click
import dotenv

import designate.deployment
import designate.errors
import designate.registry

dotenv.load_dotenv()


@click.group()
def cli():
    pass


@click.command()
@click.option("--registry-repo", type=str, required=True, envvar="REGISTRY_REPO")
@click.option("--registry-branch", type=str, required=True, envvar="REGISTRY_BRANCH")
@click.option("--github-token", type=str, envvar="GITHUB_TOKEN")
@click.option("--github-app-id", type=int, envvar="GITHUB_APP_ID")
@click.option("--github-app-private-key", type=str, envvar="GITHUB_APP_PRIVATE_KEY")
@click.option("--chart", type=str, required=True)
@click.option("--pipeline", type=str, required=True)
@click.option("--environment", type=str, required=True)
@click.option("--version", type=str, required=True)
@click.option("--name", type=str, required=True)
def deploy(
    name: str,
    version: str,
    environment: str,
    pipeline: str,
    chart: str,
    registry_repo: str,
    registry_branch: str,
    github_token: str = None,
    github_app_id: int = None,
    github_app_private_key: str = None,
):
    click.echo(
        f"Designating deployment of {name} ({version}) on {environment} environment"
    )
    click.echo(f"Using {chart} chart, deployment method is {pipeline}")
    if github_token:
        token = github_token
    else:
        click.echo("Detected GitHub app credentials, generating temporary token...")
        token = designate.registry.GithubApp(github_app_id, github_app_private_key, registry_repo).token  # type: ignore
    registry = designate.registry.Registry(token, registry_repo, registry_branch)
    for app in registry.apps:
        if app.name != name:
            continue
        break
    else:
        raise designate.errors.AppNotFound(app.name) from None
    args = designate.deployment.DeploymentArgs(version, environment, pipeline, chart)
    deployment = app.designate(args, registry.templates, registry.environments)
    deployment.start()
    click.echo("Done!")


@click.command()
@click.option("--registry-repo", type=str, required=True, envvar="REGISTRY_REPO")
@click.option("--registry-branch", type=str, required=True, envvar="REGISTRY_BRANCH")
@click.option("--github-token", type=str, required=True, envvar="GITHUB_TOKEN")
def lint(
    github_token: str,
    registry_repo: str,
    registry_branch: str,
):
    click.echo("Linting registry entries...")
    registry = designate.registry.Registry(github_token, registry_repo, registry_branch)
    registry.apps
    click.echo("Everything's Gucci!")


cli.add_command(deploy)
cli.add_command(lint)


if __name__ == "__main__":
    cli()
