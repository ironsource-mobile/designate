class Error(Exception):
    message = "Unknown error"
    code = "ERR_UNKNOWN"

    @property
    def text(self) -> str:
        text = f"[{self.code}]: {self.message}"
        if self.details:
            text += f": {self.details}"
        return text

    def __init__(self, details: str = ""):
        self.details = details
        super().__init__(self.message)


class GithubError(Error):
    message = "GitHub Error"
    code = "ERR_GITHUB"


class EntryError(Error):
    message = "Entry parsing error"
    code = "ERR_SYNTAX_ENTRY"


class TemplateError(Error):
    message = "Template rendering error"
    code = "ERR_SYNTAX_TEMPLATE"


class SpinnakerError(Error):
    message = "Spinnaker Error"
    code = "ERR_SPINNAKER"


class AppNotFound(Error):
    message = "App entry not found"
    code = "ERR_APP_NOT_FOUND"


class TemplateNotFound(Error):
    message = "Template not found"
    code = "ERR_TPL_NOT_FOUND"


class EnvironmentNotFound(Error):
    message = "Matching environment not found"
    code = "ERR_ENV_NOT_FOUND"
