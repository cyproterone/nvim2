from fnmatch import fnmatch
from pathlib import Path
from shutil import which
from typing import Any, Mapping, MutableMapping, Optional

from pynvim import Nvim
from pynvim_pp.api import get_cwd
from pynvim_pp.lib import write
from std2.pickle import decode, encode
from std2.types import never

from ..config.lsp import LspAttrs, RootPattern, RPFallback, lsp_specs
from ..registery import LANG, atomic, keymap, rpc

keymap.n("gp") << "<cmd>lua vim.lsp.buf.definition()<cr>"
keymap.n("gP") << "<cmd>lua vim.lsp.buf.references()<cr>"


@rpc(blocking=True)
def _find_root(nvim: Nvim, _pattern: Any, filename: str, bufnr: int) -> Optional[str]:
    pattern: RootPattern = decode(RootPattern, _pattern)
    path = Path(filename)

    for parent in path.parents:
        for member in parent.iterdir():
            name = member.name
            if name in pattern.exact:
                return str(parent)
            else:
                for glob in pattern.glob:
                    if fnmatch(name, glob):
                        return str(parent)
    else:
        if pattern.fallback is RPFallback.none:
            return None
        elif pattern.fallback is RPFallback.cwd:
            return get_cwd(nvim)
        elif pattern.fallback is RPFallback.home:
            return str(Path.home())
        elif pattern.fallback is RPFallback.parent:
            return str(path.parent)
        else:
            never(pattern)


@rpc(blocking=True)
def _on_attach(nvim: Nvim, server: str) -> None:
    write(nvim, LANG("lsp loaded", server=server))


_LSP_INIT = """
(function (root_fn, attach_fn, server, cfg, root_cfg)
  local lsp = require "lspconfig"
  local configs = require "lspconfig/configs"

  cfg.on_attach = function (client, bufnr)
    _G[attach_fn](server)
  end

  local go = lsp[server] ~= nil

  if not go then
    configs[server] = { default_config = cfg }
  end

  if root_cfg ~= vim.NIL or not go then
    cfg.root_dir = function (filename, bufnr)
        local root = _G[root_fn](root_cfg, filename, bufnr)
        return root ~= vim.NIL and root or nil
    end
  end

  lsp[server].setup(cfg)
end)(...)
"""


def _encode_spec(spec: LspAttrs) -> Mapping[str, Any]:
    config: MutableMapping[str, Any] = {}
    if spec.args is not None:
        config["cmd"] = (spec.bin, *spec.args)
    if spec.filetypes:
        config["filetypes"] = spec.filetypes
    if spec.init_options:
        config["init_options"] = spec.init_options
    if spec.settings:
        config["settings"] = spec.settings

    return config


for spec in lsp_specs:
    if which(spec.bin):
        config = _encode_spec(spec)
        args = (
            _find_root.name,
            _on_attach.name,
            spec.server,
            encode(config),
            encode(spec.root),
        )
        atomic.exec_lua(_LSP_INIT, args)

atomic.command("doautoall Filetype")
