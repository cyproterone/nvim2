from ..registery import keymap, settings


# find result during search
settings["incsearch"] = True
# search results shown on side
settings["inccommand"] = "nosplit"
# use ripgrep
settings["grepprg"] = r"rg\ --vimgrep"


# clear hlsearch result
keymap.n("<leader>i") << "<cmd>nohlsearch<cr>"


# search without moving
keymap.n("*") << "*Nzz"
keymap.n("#") << "#Nzz"
keymap.n("g*") << "g*Nzz"
keymap.n("g#") << "g#Nzz"
# centre on search result
keymap.n("n") << "nzz"
keymap.n("N") << "Nzz"


# use no magic
keymap.nv("/", silent=False) << r"/\V"
keymap.nv("?", silent=False) << r"?\V"
