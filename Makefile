.PHONY: install

install: ~/.local/bin/annot2tex

~/.local/bin/annot2tex: annot2tex.py Makefile
	echo python3 $(CURDIR)/annot2tex.py $@ > ~/.local/bin/annot2tex
	chmod u+x ~/.local/bin/annot2tex
#

