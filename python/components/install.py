from asyncio.tasks import as_completed
from datetime import datetime, timezone
from os import linesep
from shutil import which
from sys import stderr
from typing import Awaitable, Iterator, Sequence, Tuple

from pynvim.api.nvim import Nvim
from std2.asyncio.subprocess import ProcReturn, call

from ..config.fmt import fmt_specs
from ..config.install import ScriptSpec
from ..config.linter import linter_specs
from ..config.lsp import lsp_specs
from ..config.pkgs import pkg_specs
from ..consts import (
    BIN_DIR,
    GO_DIR,
    INSTALL_SCRIPT,
    LIB_DIR,
    NPM_DIR,
    PIP_DIR,
    UPDATE_LOG,
    VARS_DIR,
    VIM_DIR,
)
from ..workspace.terminal import open_term
from .rtp import p_name


def _git_specs() -> Iterator[str]:
    for spec in pkg_specs:
        yield spec.uri


def _pip_specs() -> Iterator[str]:
    for l_spec in lsp_specs:
        yield from l_spec.install.pip
    for i_spec in linter_specs:
        yield from i_spec.install.pip
    for f_spec in fmt_specs:
        yield from f_spec.install.pip


def _npm_specs() -> Iterator[str]:
    for l_spec in lsp_specs:
        yield from l_spec.install.npm
    for i_spec in linter_specs:
        yield from i_spec.install.npm
    for f_spec in fmt_specs:
        yield from f_spec.install.npm


def _go_specs() -> Iterator[str]:
    for l_spec in lsp_specs:
        yield from l_spec.install.go
    for i_spec in linter_specs:
        yield from i_spec.install.go
    for f_spec in fmt_specs:
        yield from f_spec.install.go


def _script_specs() -> Iterator[Tuple[str, ScriptSpec]]:
    for l_spec in lsp_specs:
        yield l_spec.bin, l_spec.install.script
    for i_spec in linter_specs:
        yield i_spec.bin, i_spec.install.script
    for f_spec in fmt_specs:
        yield f_spec.bin, f_spec.install.script


SortOfMonoid = Sequence[Tuple[str, ProcReturn]]


def _git() -> Iterator[Awaitable[SortOfMonoid]]:
    VIM_DIR.mkdir(parents=True, exist_ok=True)
    cmd = "git"

    if which(cmd):
        for pkg in _git_specs():

            async def cont(pkg: str) -> SortOfMonoid:
                location = VIM_DIR / p_name(pkg)
                if location.is_dir():
                    p = await call(
                        cmd, "pull", "--recurse-submodules", cwd=str(location)
                    )
                    return ((pkg, p),)
                else:
                    p = await call(
                        cmd,
                        "clone",
                        "--depth=1",
                        "--recurse-submodules",
                        "--shallow-submodules",
                        pkg,
                        str(location),
                    )
                    return ((pkg, p),)

            yield cont(pkg)


def _pip() -> Iterator[Awaitable[SortOfMonoid]]:
    PIP_DIR.mkdir(parents=True, exist_ok=True)
    cmd = "pip3"
    specs = tuple(_pip_specs())

    if which(cmd) and specs:

        async def cont() -> SortOfMonoid:
            p = await call(
                cmd,
                "install",
                "--upgrade",
                "--target",
                str(PIP_DIR),
                "--",
                *specs,
                cwd=str(PIP_DIR),
            )
            return (("", p),)

        yield cont()


def _npm() -> Iterator[Awaitable[SortOfMonoid]]:
    NPM_DIR.mkdir(parents=True, exist_ok=True)
    cmd = "npm"

    if which(cmd):

        async def cont() -> SortOfMonoid:
            p1 = await call(cmd, "init", "--yes", cwd=str(NPM_DIR))
            if p1.code:
                return (("", p1),)
            else:
                p2 = await call(
                    cmd, "install", "--upgrade", "--", *_npm_specs(), cwd=str(NPM_DIR)
                )
                return ("", p1), ("", p2)

        yield cont()


def _go() -> Iterator[Awaitable[SortOfMonoid]]:
    GO_DIR.mkdir(parents=True, exist_ok=True)
    cmd = "go"

    if which(cmd):

        async def cont() -> SortOfMonoid:
            p = await call(
                cmd,
                "get",
                "--",
                *_go_specs(),
                env={"GO111MODULE": "on", "GOPATH": str(VARS_DIR)},
                cwd=str(GO_DIR),
            )
            return (("", p),)

        yield cont()


def _script() -> Iterator[Awaitable[SortOfMonoid]]:
    for path in (LIB_DIR, BIN_DIR):
        path.mkdir(parents=True, exist_ok=True)

    for bin, pkg in _script_specs():

        async def cont(bin: str, pkg: ScriptSpec) -> SortOfMonoid:
            env = {
                "BIN_NAME": bin,
                "BIN_PATH": str(BIN_DIR / bin),
                "LIB_PATH": str(LIB_DIR / bin),
            }
            stdin = pkg.body.encode()
            p = await call(
                pkg.interpreter,
                stdin=stdin,
                env={**env, **pkg.env},
                cwd=str(VARS_DIR),
            )
            return ((pkg.body, p),)

        if which(pkg.interpreter) and pkg.body:
            yield cont(bin, pkg)


async def install() -> int:
    has_error = False
    for fut in as_completed((*_git(), *_pip(), *_npm(), *_go(), *_script())):
        for debug, proc in await fut:
            if proc.code == 0:
                print("✅ 👉", proc.prog, *proc.args)
                print(debug)
                print(proc.out.decode())
            else:
                has_error = True
                print(
                    f"⛔️ - {proc.code} 👉",
                    proc.prog,
                    *proc.args,
                    file=stderr,
                )
                print(debug, file=stderr)
                print(proc.err, file=stderr)

    return has_error


def maybe_install(nvim: Nvim) -> None:
    UPDATE_LOG.parent.mkdir(parents=True, exist_ok=True)
    before = (
        datetime.fromisoformat(UPDATE_LOG.read_text())
        if UPDATE_LOG.exists()
        else datetime(year=1949, month=9, day=21, tzinfo=timezone.utc)
    )

    now = datetime.now(tz=timezone.utc)
    diff = now - before
    if diff.days > 7:
        ans = nvim.funcs.confirm("🤖「ゴゴゴゴ」？", f"&Yes{linesep}&No", 2)
        if ans == 1:
            open_term(nvim, "python3", INSTALL_SCRIPT, "--install-packages")
            UPDATE_LOG.write_text(now.isoformat())
