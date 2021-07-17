import base64

import attr
import github


@attr.s
class GithubApp:
    app_id: int = attr.ib()
    private_key: str = attr.ib()
    repo: str = attr.ib()

    @property
    def token(self):
        private_key = base64.b64decode(self.private_key)
        app = github.GithubIntegration(self.app_id, private_key)
        owner, repo = self.repo.split("/")
        installation = app.get_installation(owner, repo)
        token = app.get_access_token(installation.id)
        return token
