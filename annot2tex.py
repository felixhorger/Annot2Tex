import os
import shutil
import subprocess
import re
import argparse
from itertools import groupby
import fitz


def get_highlighted_text(page, rect):
	words = page.get_text("words")
	# Sort ascending y, then x
	words.sort(key=lambda w: (w[3], w[0]))
	words = [w for w in words if fitz.Rect(w[:4]).intersects(rect)]
	# Group by y
	groups = groupby(words, key=lambda w: w[3])
	# Return text split into lines
	return [" ".join(w[4] for w in g) for _, g in groups]
#



# fitz -> coordinate of annot -> synctex -> file & line     BUT   where to put in that line?
# could do: fitz -> coordinate of annot -> words intersecting
# but better is to use margin comment
#TODO: highlight comments (how to differentiate highlight, strikethourgh...?)
#TODO: insert comments
#that should be enough, but could test scribbles, 

def syncin2tex(pdfpath, synctexpath, root, buildcmd, authordict):

	doc = fitz.open(pdfpath) # This file can be anywhere, hence read that first according to the user's input

	os.chdir(root) # Then cd to the root directory of the tex project

	synctexfilename = os.path.basename(synctexpath)
	synctexdir = os.path.relpath(os.path.dirname(synctexpath), root)

	# For parsing synctex's output
	regex_file = re.compile("Input:(.*)")
	regex_line = re.compile("Line:([0-9]*)")

	texfiles = {}

	for page in doc:
		for annot in page.annots():
			if annot.info["subject"] == "1": continue
			# Adobe adds an id, but pdfcomment.sty doesn't (grumble mumble...),
			# misusing subject to remember which have been synced already

			# Find file and line using synctex
			# Get coordinates of annotation
			x = 0.5 * (annot.rect.x0 + annot.rect.x1)
			y = 0.5 * (annot.rect.y0 + annot.rect.y1)
			#print(annot.info["content"], annot.rect)
			# Run synctex
			cmd = ["synctex", "edit", "-o", "%d:%.2f:%.2f:%s" % (1+page.number, x, y, synctexfilename), "-d", synctexdir]
			#print(" ".join(cmd)) # TODO: use logging
			p = subprocess.run(cmd, stdout=subprocess.PIPE)
			synctexout = p.stdout.decode()
			#print(synctexout)
			# Parse output
			m = re.search(regex_file, synctexout)
			texfile = m.group(1)
			m = re.search(regex_line, synctexout)
			#print(m)
			lineno = int(m.group(1)) - 1 # one based indexing
			#print(lineno)

			if texfile in texfiles: texlines = texfiles[texfile]
			else:
				f = open(texfile, "r")
				texlines = f.readlines()
				texfiles[texfile] = texlines
				f.close()
			#

			# TODO copy date
			if annot.type[0] == fitz.PDF_ANNOT_TEXT:
				# Is it a reply?
				annot_tex = "\marginpar{"
				if annot.irt_xref == 0: annot_tex += "\pdfcomment[hoffset=2cm," # TODO: make these options accessible
				else:                   annot_tex += "\pdfreply[hoffset=2cm,replyto=%d," % annot.irt_xref
				# Add info
				annot_tex += "id=%d,avatar={%s},subject=1]{%s}}\hskip-\lastskip\n" % (
					annot.xref,
					authordict.get(annot.info["title"], "Chuck Norris"),
					annot.info["content"]
				)
				#print(annot_tex)
				# Adjust line
				if lineno == 0: lineno = 1
				texlines[lineno-1] += annot_tex
			#
			elif annot.type[0] == fitz.PDF_ANNOT_HIGHLIGHT:
				print("asd")
			 	#x = 0.5 * (annot.rect.x0 + annot.rect.x1)
				#y = 0.5 * (annot.rect.y0 + annot.rect.y1)
				#print_highlighted_text(page, annot.rect)
				#cmd = ["synctex", "edit", "-o", "%d:%.2f:%.2f:%s" % (1+page.number, x, y, "main.pdf"), "-d", "aux"]
				#print(" ".join(cmd))
				#p = subprocess.run(cmd, stdout=subprocess.PIPE)
				#s = p.stdout.decode()
				#print(s)
				#m = re.search(regex, s)
				#print(m.group(1))
			else:
				raise Exception("Unknown annotation type %s" % annot.type[1])
			#

			#for l in texlines: print(l, end="")
		#
	#
	doc.close()

	# Backup originals and write changes
	for texfile, texlines in texfiles.items():
		backup = texfile + ".bak"
		if os.path.exists(backup): raise Exception("Backup file exists, please clean that up first")
		shutil.copyfile(texfile, backup)
		f = open(texfile, "w")
		f.writelines(texlines)
		f.close()
	#

	# TODO: check y coordinates of annots generated (and page), make this possible by adding an option alike -cmd="make main.pdf" and then analyse new pdf

	return
#





parser = argparse.ArgumentParser(
	prog="Sync into Tex",
	description="Extracts annotations from a PDF and places them at the correct location in that PDF's LaTex code"
)

# Need: pdf, directory containing tex and synctex files
parser.add_argument("pdf", help="Path to PDF file containing annotations")
parser.add_argument("synctex", help="Path to the synctex file")
parser.add_argument("root", help="Root path of the LaTex project of that PDF")
parser.add_argument("-b", "--buildcmd", help="command to build the PDF, which can be used to check the synchronised comments")
parser.add_argument("-a", "--authordict", help="YAML file containing a dictionary translating author names to pdfcomment.sty avatar names as defined in the tex project")
args = parser.parse_args()

# TODO: parse YAML authors

syncin2tex(args.pdf, args.synctex, args.root, args.buildcmd, {})

