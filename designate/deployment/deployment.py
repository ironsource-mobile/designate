import attr
import click

import designate.registry
from designate.deployment.spinnaker import Pipeline


@attr.s
class Deployment:
    app: "designate.registry.App" = attr.ib()
    args: "DeploymentArgs" = attr.ib()
    environment: "designate.registry.Environment" = attr.ib()
    values: str = attr.ib()

    def start(self) -> None:
        click.echo(f"Going to deploy on {self.environment.name} now")
        pipeline = Pipeline(self.args.pipeline)
        pipeline.run(
            self.app.name,
            self.environment.spinnaker_url,
            self.values,
            self.args.serialized,
        )


@attr.s
class DeploymentArgs:
    version: str = attr.ib()
    environment: str = attr.ib()
    pipeline: str = attr.ib()
    chart: str = attr.ib()

    @property
    def serialized(self) -> dict[str, str]:
        return {
            "version": self.version,
            "environment": self.environment,
            "pipeline": self.pipeline,
            "chart": self.chart,
        }
