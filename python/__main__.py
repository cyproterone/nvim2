from argparse import ArgumentParser, Namespace
from sys import path
from typing import Literal, Union

from python.consts import REQUIREMENTS, RT_DIR

RT_DIR.mkdir(parents=True, exist_ok=True)
path.append(str(RT_DIR))


def parse_args() -> Namespace:
    parser = ArgumentParser()

    sub_parsers = parser.add_subparsers(dest="command", required=True)

    s_run = sub_parsers.add_parser("run")
    s_run.add_argument("--socket", required=True)

    s_deps = sub_parsers.add_parser("deps")
    s_deps.add_argument("deps", nargs="*", default=())

    return parser.parse_args()


args = parse_args()
command: Union[Literal["deps"], Literal["run"]] = args.command

if command == "deps":
    from typing import Sequence

    deps: Sequence[str] = args.deps

    if not deps or "runtime" in deps:
        from subprocess import run

        proc = run(
            (
                "pip3",
                "install",
                "--upgrade",
                "--target",
                str(RT_DIR),
                "--requirement",
                REQUIREMENTS,
            ),
            cwd=str(RT_DIR),
        )
        if proc.returncode:
            exit(proc.returncode)

    if not deps or "packages" in deps:
        from asyncio import run as arun

        from python.components.install import install

        code = arun(install())
        if code:
            exit(code)

elif command == "run":
    from pynvim import attach
    from pynvim_pp.client import run_client

    from python.client import Client

    nvim = attach("socket", path=args.socket)
    code = run_client(nvim, client=Client())
    exit(code)

else:
    assert False
