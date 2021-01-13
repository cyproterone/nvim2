from collections import Counter

from pynvim.api.nvim import Nvim
from pynvim_pp.api import (
    buf_get_lines,
    cur_window,
    win_get_buf,
    win_get_cursor,
    win_set_cursor,
)
from pynvim_pp.lib import async_call, go

from ..registery import autocmd, rpc

_CHAR_PAIRS = {'"': '"', "'": "'", "`": "`", "(": ")", "{": "}", "<": ">"}


@rpc(blocking=True)
def _surround(nvim: Nvim) -> None:
    lhs: str = nvim.vvars["char"]
    rhs = _CHAR_PAIRS.get(lhs)

    if rhs:
        win = cur_window(nvim)
        buf = win_get_buf(nvim, win=win)
        row, col = win_get_cursor(nvim, win=win)
        lines = buf_get_lines(nvim, buf=buf, lo=row, hi=row + 1)
        line = next(iter(lines))

        def cont() -> None:
            new_col = col + len(lhs.encode())
            nvim.api.set_vvar("char", lhs + rhs)
            set_cur = lambda: win_set_cursor(nvim, win=win, row=row, col=new_col)
            go(async_call(nvim, set_cur))

        if rhs == lhs:
            odd_one_out = line.count(lhs) % 2 == 0
            if odd_one_out:
                cont()
        else:
            counts = Counter(line)
            if counts[lhs] >= counts[rhs]:
                cont()


autocmd("InsertCharPre") << f"lua {_surround.name}()"
