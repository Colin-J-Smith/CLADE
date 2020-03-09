" Name this file .vimrc (the dot is important) and put it in your home directory

" GENERAL OPTIONS
behave xterm
set viminfo='20,\"500,%	" ' Maximum number of previously edited files for which
                        "   the marks are remembered.  
			" " Maximum number of lines saved for each register.
			" % When included, save and restore the buffer list.
                        "   If Vim is started with a file name argument, the
                        "   buffer list is not restored.  If Vim is started
                        "   without a file name argument, the buffer list is
                        "   restored from the viminfo file.  Buffers without a
                        "   file name and buffers for help files are not written
			"   to the viminfo file.
set history=500		" keep {number} lines of command line history

" TAB HANDLING, program formatting:
set tabstop=8		" ts, number of spaces that a tab *in an input file* is
                        "   equivalent to.
set shiftwidth=4	" sw, number of spaces shifted left and right when
                        "   issuing << and >>
			"  commands
set smarttab            " a <Tab> in an indent inserts 'shiftwidth' spaces
set softtabstop=4       " number of spaces that a tab *pressed by the user*
                        "   is equivalent to
set shiftround          " round to 'shiftwidth' for "<<" and ">>"
set expandtab           " don't input tabs; replace with spaces. <local to
                        "   buffer>

" see Vim book p 71 for this
filetype on
au BufRead,BufNewFile *.py set expandtab
autocmd FileType * set formatoptions=tcql nocindent comments&
" Formatoptions: 'q' allows formatting with "gq".  'r' automates the middle of
"    a comment.  'o' automates comment formatting with the 'o' or 'O'
"    commands.  'c' wrap comments.  'l' do not break lines in insert mode.
set autoindent          " automatically set the indent of a new line (local to
                        "   buffer)
set smartindent         " autoindenting (local to buffer); let cindent

set wrap                " whether to wrap lines
" Make breaks more obvious
"set showbreak=+++\ \  
" set number		" number lines
set nocompatible
set incsearch
set showmatch
set backspace=1

syntax on               " colorize
set statusline=%f%m%r%h%w\ %R%M\ [POS=%04l,%04v][%p%%]\ [LEN=%L]
set laststatus=2 " always show the status line

" VIM DISPLAY OPTIONS
set showmode		" show which mode (insert, replace, visual)
set ruler
set title
set showcmd		" show commands in status line when typing
set wildmenu	

" KEY MAPPINGS
"   depending on your terminal software, you may have to fiddle with a few
"   things to make it look right for you.  It works for me logged in through
"   SSH.

"  F6 Clears up formatting by doing the following:
"  Ensure UNIX formatting (no CR chars, NL after the last line).
"  Insert a tab at the end of the current line (to avoid errors in next
"      step).
"  Then replace all tabs with 4 spaces.  That is, "detab".
"  Then, remove any spaces at the end of lines (this corrects the inserted
"      tab).
"  Then, clean up some annoying highlights in the file.
"  Note: this detabbing should work for tabs at the beginning of the line, but
"      will probably be somewhat wrong for tabs later in the line, but
"      wherever they used to be, they'll now be gone.
:map <F6> mzA	<esc>:set fileformat=unix<cr>:set endofline<cr>:%s/	/    /g<cr>:%s/ *$//<cr>:nohlsearch<cr>i<esc>`z

:imap <F6> <esc>mzA	<esc>:set fileformat=unix<cr>:set endofline<cr>:%s/	/    /g<cr>:%s/ *$//<cr>:nohlsearch<cr>i<esc>`za

"  Useful for limiting lines to 80 columns.  Goes to column 80, then back to a
"      previous space, then changes that space to a newline.  "autoindent" from
"      above completes this trick.
:map <F7> 80|F s<cr><esc>
:map <S-F7> 80|F s<cr><tab><esc>
:set backspace=indent,eol,start
:set number
set mouse=a

set textwidth=79
set cc=+1

" from Jones
" Misc vim stuff
set nocompatible
set nomodeline

" Turns on indentation settings based on the filetype
filetype plugin indent on

" Color stuff
syntax on
set nohls

" If not all colors are enabled, enable all colors
if &t_Co < 256
   set t_Co=256
endif

" Turn on line numbers
set number

" Allow normal backspace behaviour in insert mode
set backspace=indent,eol,start
set whichwrap+=<,>

" Autoindent copies the indentation from the previous line
set autoindent

" Tabbing stuff
" softtabstop (sts) sets how many spaces a tab should appear to be
" shiftwidth (sw) sets how many spaces text is indented
" expandtab (et) makes vim use spaces instead of tabs
" Basically this allows for spaces instead of tabs
set softtabstop=3 shiftwidth=3 expandtab
set smarttab
set shiftround

" Does incremental searching
set incsearch

" Show the status bar
" ruler displays the cursor position at all times
" showcmd displays incomplete commands
set ruler
set showcmd

" Change timeout options
set ttimeoutlen=100
set timeoutlen=3000

" Makes it easier to more around long lines
noremap <Up> g<Up>
inoremap <Up> <esc>g<Up>a
noremap <Down> g<Down>
inoremap <Down> <esc>g<Down>a
noremap j gj
noremap k gk

" Enable mouse
if has('mouse')
   set mouse=a
endif

" Official python style is 4 spaces rather that 3
autocmd FileType python setlocal sts=4 sw=4

set clipboard+=unnamedplus  " use the clipboards of vim and win
set paste               " Paste from a windows or from vim
set go+=a               " Visual selection automatically copied to the clipboard
