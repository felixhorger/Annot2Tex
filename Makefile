.PHONY: install readme

install: ~/.local/bin/annot2tex

~/.local/bin/annot2tex: annot2tex.py Makefile
	echo python3 $(CURDIR)/annot2tex.py $@ > ~/.local/bin/annot2tex
	chmod u+x ~/.local/bin/annot2tex
#

readme: README.html

README.html: README.md Makefile
	pandoc README.md > README.html
#

