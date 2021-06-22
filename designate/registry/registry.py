import attr
import click
import deserialize  # type: ignore
import github
import github.ContentFile
import jinja2
import yaml

import designate.deployment
import designate.errors


@attr.s
class Registry:
    token: str = attr.ib()
    repo: str = attr.ib()
    branch: str = attr.ib(default="main")

    @property
    def ghub(self) -> github.Github:
        try:
            return self._ghub  # type: ignore
        except AttributeError:
            self._ghub = github.Github(self.token)
            return self._ghub

    @property
    def apps(self) -> list["App"]:
        try:
            return self._apps  # type: ignore
        except AttributeError:
            self._apps = [entry for entry in self.entries if isinstance(entry, App)]
            return self._apps

    @property
    def templates(self) -> list["Template"]:
        try:
            return self._templates  # type: ignore
        except AttributeError:
            self._templates = [
                entry for entry in self.entries if isinstance(entry, Template)
            ]
            return self._templates

    @property
    def environments(self) -> list["Environment"]:
        try:
            return self._environments  # type: ignore
        except AttributeError:
            self._environments = [
                entry for entry in self.entries if isinstance(entry, Environment)
            ]
            return self._environments

    @property
    def entries(self) -> list["Entry"]:
        try:
            return self._entries  # type: ignore
        except AttributeError:
            try:
                click.echo("Loading registry entries", nl=False)
                repo = self.ghub.get_repo(self.repo)
                contents = repo.get_contents("", ref=self.branch)
                self._entries: list["Entry"] = list()
                while contents:
                    f_content = contents.pop(0)  # type: ignore
                    if f_content.type == "dir":
                        contents.extend(repo.get_contents(f_content.path, ref=self.branch))  # type: ignore
                        continue
                    if not f_content.name.endswith((".yaml", ".yml")):
                        continue
                    entry_data = yaml.safe_load(f_content.decoded_content)  # type: ignore
                    entry = deserialize.deserialize(Entry, entry_data)
                    self._entries.append(entry)
                    click.echo(".", nl=False)
                click.echo("ok")
                return self._entries
            except github.GithubException as exc:
                click.echo("failed")
                raise designate.errors.GithubError(str(exc)) from None
            except (yaml.YAMLError, deserialize.DeserializeException) as exc:
                click.echo("failed")
                raise designate.errors.EntryError(
                    f_content.path + ": " + str(exc)
                ) from None


@deserialize.downcast_field("kind")
@attr.s
class Entry:
    name: str = attr.ib()


@deserialize.downcast_identifier(Entry, "environment")
@attr.s
class Environment(Entry):
    environment: str = attr.ib()
    tags: dict = attr.ib()
    domain: str = attr.ib()
    spinnaker_url: str = attr.ib()

    def match(self, app: "App") -> bool:
        for tag, value in self.tags.items():
            if app.tags.get(tag, "") != value:
                return False
        return True

    @property
    def serialized(self) -> dict:
        return {
            "name": self.name,
            "environment": self.environment,
            "tags": self.tags,
            "domain": self.domain,
        }


@deserialize.downcast_identifier(Entry, "template")
@attr.s
class Template(Entry):
    template: str = attr.ib()

    def render(
        self,
        app: "App",
        args: "designate.deployment.DeploymentArgs",
        environment: "Environment",
    ) -> str:
        env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
        )
        click.echo("Rendering values...", nl=False)
        try:
            rendered = env.from_string(self.template).render(
                app=app.serialized,
                deployment=args.serialized,
                environment=environment.serialized,
            )
            click.echo("ok")
            return rendered
        except jinja2.TemplateError as exc:
            click.echo("failed")
            raise designate.errors.TemplateError(str(exc)) from None


@deserialize.downcast_identifier(Entry, "app")
@attr.s
class App(Entry):
    template: str = attr.ib()
    tags: dict = attr.ib()

    def designate(
        self,
        args: "designate.deployment.DeploymentArgs",
        templates: list["Template"],
        environments: list["Environment"],
    ) -> "designate.deployment.Deployment":
        click.echo("Matching environments...", nl=False)
        for environment in environments:
            if not environment.match(self):
                continue
            if args.environment != environment.environment:
                continue
            break
        else:
            click.echo("failed")
            raise designate.errors.EnvironmentNotFound(
                args.environment + ", " + str(self.tags)
            ) from None
        click.echo("ok")
        click.echo("Matching templates...", nl=False)
        for template in templates:
            if template.name != self.template:
                continue
            break
        else:
            click.echo("failed")
            raise designate.errors.TemplateNotFound(self.template) from None
        click.echo("ok")
        values = template.render(self, args, environment)
        return designate.deployment.Deployment(self, args, environment, values)

    @property
    def serialized(self) -> dict:
        return {"name": self.name, "tags": self.tags}
