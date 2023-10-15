from typing import List, Optional
import click
import logging

logger = logging.getLogger(__package__)


class TagList(click.ParamType):
    """
    Converts accepted text 'tag,name,etc' into individual components.
    """
    name="tag"
    def convert(self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> List[str]:
        if isinstance(value, str):
            return value.split(",")
        self.fail(f"{value} is not a valid string", param, ctx)