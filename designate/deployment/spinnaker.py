import base64

import attr
import click
import requests

import designate.errors

SPINNAKER_HTTP_TIMEOUT = 5.0


@attr.s
class Pipeline:
    name: str = attr.ib()

    def run(self, app_name: str, spinnaker_url: str, values: str, args: dict) -> None:
        webhook_name = f"app.{app_name}.{self.name}"
        url = f"{spinnaker_url}/webhooks/webhook/{webhook_name}"
        values_b64 = base64.b64encode(values.encode()).decode()
        payload = {
            "artifacts": [
                {
                    "type": "embedded/base64",
                    "reference": values_b64,
                    "name": "registry-values",
                }
            ],
            "parameters": args,
        }
        click.echo(f"Triggering Spinnaker webhook {webhook_name}...", nl=False)
        try:
            response = requests.post(url, json=payload, timeout=SPINNAKER_HTTP_TIMEOUT)
            click.echo(str(response.status_code))
            response.raise_for_status()
        except requests.RequestException as exc:
            raise designate.errors.SpinnakerError(str(exc)) from None
