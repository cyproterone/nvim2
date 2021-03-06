from typing import Sequence

from std2.pickle import new_decoder
from yaml import safe_load

from ..consts import CONF_TOOL
from .install import InstallSpec

ToolSpecs = Sequence[InstallSpec]
tool_specs: ToolSpecs = new_decoder(ToolSpecs)(safe_load(CONF_TOOL.open()))

