from typing import Iterator, Sequence, Tuple

from pynvim import Nvim
from pynvim.api.nvim import Buffer, Nvim
from pynvim_pp.api import (
    buf_get_lines,
    buf_get_option,
    buf_set_lines,
    cur_buf,
    cur_win,
    win_get_buf,
    win_get_cursor,
)
from pynvim_pp.operators import VisualTypes, operator_marks, writable

from ..registery import keymap, rpc


def _parse_comment_str(nvim: Nvim, buf: Buffer) -> Tuple[str, str]:
    comment_str: str = buf_get_option(nvim, buf=buf, key="commentstring")
    assert len(comment_str.splitlines()) == 1
    lhs, _, rhs = comment_str.partition("%s")
    return lhs, rhs


def _p_indent(line: str) -> str:
    spaces = "".join(c for c in line if c.isspace())
    return spaces


def _comm(
    lhs: str, rhs: str, lines: Sequence[str]
) -> Iterator[Tuple[bool, str, str, str]]:
    assert len(lhs + rhs) == 1
    assert (lhs + rhs).strip() == (lhs + rhs)

    for line in lines:
        enil = "".join(reversed(line))
        indent_f, indent_b = _p_indent(line), _p_indent(enil)

        significant = line[indent_f:indent_b]
        is_comment = significant.startswith(lhs) and significant.endswith(rhs)
        added = ""
        stripped = ""
        yield is_comment, line, added, stripped


def _toggle_comment(lhs: str, rhs: str, lines: Sequence[str]) -> Sequence[str]:
    commented = _comm(lhs, rhs, lines=lines)
    if all(com for com, _, _, _ in commented):
        return tuple(stripped for _, _, _, stripped in commented)
    elif any(com for com, _, _, _ in commented):
        return tuple(
            original if com else added for com, original, added, _ in commented
        )
    else:
        return tuple(added for _, _, added, _ in commented)


@rpc(blocking=True)
def _comment(nvim: Nvim, visual: VisualTypes = None) -> None:
    buf = cur_buf(nvim)
    if not writable(nvim, buf=buf):
        return
    else:
        (row1, _), (row2, _) = operator_marks(nvim, buf=buf, visual_type=visual)
        lines = buf_get_lines(nvim, buf=buf, lo=row1, hi=row2 + 1)
        lhs, rhs = _parse_comment_str(nvim, buf=buf)
        new_lines = _toggle_comment(lhs, rhs, lines=lines)
        buf_set_lines(nvim, buf=buf, lo=row1, hi=row2 + 1, lines=new_lines)


keymap.n("gc") << f"<cmd>set opfunc={_comment.name}<cr>g@"
keymap.v("gc") << f"<esc><cmd>lua {_comment.name}()<cr>"


@rpc(blocking=True)
def _comment_single(nvim: Nvim) -> None:
    win = cur_win(nvim)
    buf = win_get_buf(nvim, win=win)
    if not writable(nvim, buf=buf):
        return
    else:
        row, _ = win_get_cursor(nvim, win=win)
        lines = buf_get_lines(nvim, buf=buf, lo=row, hi=row + 1)
        lhs, rhs = _parse_comment_str(nvim, buf=buf)
        new_lines = _toggle_comment(lhs, rhs, lines=lines)
        buf_set_lines(nvim, buf=buf, lo=row, hi=row + 1, lines=new_lines)


keymap.n("gcc") << f"<cmd>lua {_comment_single.name}()<cr>"