from typing import Any

from django.template import Context, Template


class MessageRenderer:
    """
    Template render and transform HTML-like tags  to text format
    """
    def __init__(self, tab_size: int = 2,strip_newlines: bool = True):
        self.strip_newlines = strip_newlines
        self.tab_size = tab_size

    def render(self, template: str, context: dict[str, Any]) -> str:
        text = Template(template).render(Context(context))
        return self._postprocess(text)

    def _postprocess(self, text: str) -> str:
        text = (text
                .replace("\r", "")
                .replace("<br>", "\n")
                .replace("<tab>", " " * self.tab_size)
                )
        if self.strip_newlines:
            lines = [line.strip() for line in text.split("\n")]
            text = "\n".join([line for line in lines if line])
        return text
