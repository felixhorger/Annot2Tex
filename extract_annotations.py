import os
from itertools import groupby
import fitz
import subprocess
import re

#filename = "/mnt/c/Users/fh20local/Desktop/thesis.pdf"
#path = os.path.expanduser("%s/Desktop" % os.environ["WIN"])
path = os.path.expanduser("~/thesis")
os.chdir(path)

# Doesn't work yet, needed?
#def find_neighbour_words(page, rect):
#	words = page.get_text("words")
#	words = [w for w in words if fitz.Rect(w[:4]).intersects(rect)]
#	#fitz.Rect(0.5*(rect.x1+rect.x0)-50, 0.5*(rect.y1+rect.y0)-1, 0.5*(rect.x1+rect.x0)+50, 0.5*(rect.y1+rect.y0)+2)
#	# Sort ascending y, then x
#	words.sort(key=lambda w: (w[3], w[0]))
#	# Group by y
#	group = groupby(words, key=lambda w: w[3])
#	for y, gwords in group:
#		print(" ".join(w[4] for w in gwords))
#

def print_highlighted_text(page, rect):
	words = page.get_text("words")
	words.sort(key=lambda w: (w[3], w[0])) # ascending y, then x
	words = [w for w in words if fitz.Rect(w[:4]).intersects(rect)]
	groups = groupby(words, key=lambda w: w[3])
	for y, g in groups:
		print(" ".join(w[4] for w in g))

# fitz -> coordinate of annot -> synctex -> file & line     BUT   where to put in that line?
# could do: fitz -> coordinate of annot -> words intersecting
# but better is to use margin comment





#TODO: find two surrounding words, then use that and the line number obtained from synctex to position comment
#TODO: highlight comments (how to differentiate highlight, strikethourgh...?)
#TODO: insert comments
#that should be enough, but could test scribbles, 


regex = re.compile("Input:(.*)")

doc = fitz.open("main.pdf")
for page in doc:
	for annot in page.annots():
		if annot.info["subject"] == "1": continue # Adobe adds an id, but pdfcomment.sty doesn't (grumble mumble...)
		print(annot.type)
		print(annot.info)
		print(annot.info["id"])
		#print(annot.xref)
		#print(annot.irt_xref)
		if annot.type[0] == fitz.PDF_ANNOT_HIGHLIGHT:
			x = 0.5 * (annot.rect.x0 + annot.rect.x1)
			y = 0.5 * (annot.rect.y0 + annot.rect.y1)
			print_highlighted_text(page, annot.rect)
			cmd = ["synctex", "edit", "-o", "%d:%.2f:%.2f:%s" % (1+page.number, x, y, "main.pdf"), "-d", "aux"]
			print(" ".join(cmd))
			p = subprocess.run(cmd, stdout=subprocess.PIPE)
			s = p.stdout.decode()
			print(s)
			m = re.search(regex, s)
			print(m.group(1))
		else:
			print(annot.rect)
			x = 0.5 * (annot.rect.x0 + annot.rect.x1)
			y = 0.5 * (annot.rect.y0 + annot.rect.y1)
			#print_highlighted_text(page, annot.rect)
			#print(page.number, x, " ", y)
			cmd = ["synctex", "edit", "-o", "%d:%.2f:%.2f:%s" % (1+page.number, x, y, "main.pdf"), "-d", "aux"]
			print(" ".join(cmd))
			p = subprocess.run(cmd, stdout=subprocess.PIPE)
			s = p.stdout.decode()
			print(s)
			m = re.search(regex, s)
			print(m.group(1))

doc.close()


# TODO: check y coordinates of annots generated (and page), make this possible by adding an option alike -cmd="make main.pdf" and then analyse new pdf
