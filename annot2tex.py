import os
import shutil
import subprocess
import re
import argparse
import warnings
from pylatexenc.latexencode import unicode_to_latex
import fitz


latex_regexes = [
	('\'',   re.compile(r'{\\textquoteright}')),
	('`',    re.compile(r'{\\textquoteleft}')),
	('\'\'', re.compile(r'{\\textquotedblright}')),
	('``',   re.compile(r'{\\textquotedblleft}')),
	(r'\1',  re.compile(r'{([\\a-zA-Z]+)}'))
]
def unicode2latex(s):
	s = unicode_to_latex(
		s,
		non_ascii_only=True,
		replacement_latex_protection='braces-all',
		unknown_char_warning=True
	)
	for (sub, regex) in latex_regexes: s = regex.sub(sub, s)
	return s
#

regex_synctex_file = re.compile('Input:(.*)')
regex_synctex_line = re.compile('Line:([0-9]+)')
def texpos(pageno, x, y, synctexfilename, synctexdir):
	cmd = ['synctex', 'edit', '-o', '%d:%.2f:%.2f:%s' % (1+pageno, x, y, synctexfilename), '-d', synctexdir]
	#print(' '.join(cmd)) # TODO: use logging
	p = subprocess.run(cmd, stdout=subprocess.PIPE)
	synctexout = p.stdout.decode()
	#print(synctexout)
	# Parse output
	m = re.search(regex_synctex_file, synctexout)
	texfile = m.group(1)
	m = re.search(regex_synctex_line, synctexout)
	lineno = int(m.group(1)) # One based
	return texfile, lineno
#

# Works so lala, not because of me, just gives bounding box ... :(
#regex_synctex_page = re.compile('Page:([0-9]+)')
#regex_synctex_x = re.compile('x:([0-9.]+)')
#regex_synctex_y = re.compile('y:([0-9.]+)')
#regex_synctex_vertical = re.compile('v:([0-9.]+)')
#regex_synctex_horizontal = re.compile('h:([0-9.]+)')
#regex_synctex_height = re.compile('H:([0-9.]+)')
#def pdfpos(lineno, col, texfile, synctexfilename, synctexdir):
#	# TODO: for some reason it doesn't eat the page number (which I could know here ...), does work anyways
#	cmd = ['synctex', 'view', '-i', '%d:%d:%s' % (lineno, col, texfile), '-o', synctexfilename, '-d', synctexdir]
#	#print(' '.join(cmd)) # TODO: use logging
#	p = subprocess.run(cmd, stdout=subprocess.PIPE)
#	synctexout = p.stdout.decode()
#	print(synctexout)
#	# Parse output
#	# TODO: could do this better? Maybe go through lines and match list of regexes in large if block
#	m = re.search(regex_synctex_page, synctexout)
#	page = m.group(1) # One based
#	m = re.search(regex_synctex_x, synctexout)
#	x = float(m.group(1))
#	m = re.search(regex_synctex_y, synctexout)
#	y = float(m.group(1))
#	m = re.search(regex_synctex_height, synctexout)
#	H = float(m.group(1))
#	m = re.search(regex_synctex_vertical, synctexout)
#	v = float(m.group(1))
#	m = re.search(regex_synctex_horizontal, synctexout)
#	h = float(m.group(1))
#	return page, x, y#-0.5*H
##


def open_texfile(texfile, texfiles):
	if texfile in texfiles: texlines = texfiles[texfile]
	else:
		f = open(texfile, 'r')
		texlines = f.readlines()
		texfiles[texfile] = texlines
		f.close()
	#
	return texlines
#


def get_highlighted_text(annot):
	num_lines = len(annot.vertices) // 4
	words = annot.parent.get_text('words')
	highlighted_lines = []
	#full_lines = []
	for l in range(num_lines):
		v = 4 * l
		# Extract marked text
		rect = fitz.Rect(annot.vertices[v][0], annot.vertices[v][1], annot.vertices[v+3][0], annot.vertices[v+3][1]) # This causes comma to be included if adjacent...
		highlighted_lines.append(' '.join(w[4] for w in words if fitz.Rect(w[:4]).intersects(rect)))
		# Extract full line (required if multiple similar words are in that texline)
		#rect = fitz.Rect(page.rect.x0, annot.vertices[v][1], page.rect.x1, annot.vertices[v+3][1])
		#for w in words:
		#	word_rect = fitz.Rect(w[:4])
		#	if word_rect.intersects(rect): full_lines.append(word_rect)
		##
	#
	return highlighted_lines #, full_lines
#

markup_types = {
	fitz.PDF_ANNOT_HIGHLIGHT: 'Highlight',
	fitz.PDF_ANNOT_STRIKE_OUT: 'StrikeOut',
	fitz.PDF_ANNOT_UNDERLINE: 'Underline',
	fitz.PDF_ANNOT_SQUIGGLY: 'Squiggly'
}


# Removes LaTex comments
def cut_tex_comment(texline):
	c = texline.find('%')
	if c != -1: texline = texline[:c]
	return texline
#

def first_non_whitespace(texline):
	m = re.search('\S', texline)
	if m is None: return -1
	else:         return m.start()
#

def annot2tex(pdfpath, synctexpath, root, buildcmd, authordict):

	doc = fitz.open(pdfpath) # This file can be anywhere, hence read that first according to the user's input

	os.chdir(root) # Then cd to the root directory of the tex project

	synctexfilename = os.path.basename(synctexpath)
	synctexdir = os.path.relpath(os.path.dirname(synctexpath), root)

	texfiles = {}

	for page in doc:
		for annot in page.annots():
			if annot.info['subject'][:9] == 'ANNOT2TEX': continue
			# Adobe adds an id, but pdfcomment.sty doesn't (grumble mumble...),
			# misusing subject to remember which have been synced already

			#
			# ---------- COMMENT BOX ANNOTATIONS ----------
			#
			if annot.type[0] == fitz.PDF_ANNOT_TEXT:
				# Find file and line using synctex
				# Get coordinates of annotation
				x = 0.5 * (annot.rect.x0 + annot.rect.x1)
				y = 0.5 * (annot.rect.y0 + annot.rect.y1)
				texfile, lineno = run_synctex(page.number, x, y, synctexfilename, synctexdir)
				texlines = open_texfile(texfile, texfiles)

				# Is it a reply?
				annot_tex = '\marginpar{'
				if annot.irt_xref == 0: annot_tex += '\pdfcomment[hoffset=2cm,' # TODO: make these options accessible
				else:                   annot_tex += '\pdfreply[hoffset=2cm,replyto=%d,' % annot.irt_xref
				# Add info
				annot_tex += 'id=%d,avatar={%s},date={%s},subject={ANNOT2TEX%s}]{%s}}\hskip-\lastskip\n' % (
					annot.xref,
					authordict.get(annot.info['title'], 'ChuckNorris'),
					annot.info['modDate'],
					annot.info['id'],
					annot.info['content']
				)
				# Adjust line
				if lineno == 0: lineno = 1
				texlines[lineno-1] += annot_tex
			#
			# ---------- HIGHLIGHT ANNOTATIONS ----------
			#
			elif annot.type[0] in markup_types:

				highlighted_pdflines = get_highlighted_text(annot)
				# Problem is that this gives lines in PDF but need lines in Tex

				# Reconstruct the latex code corresponding to the highlighted text
				# This is required because the line breaks in LaTex/PDF are different and e.g. hyphens can be introduced in PDF
				highlighted_texlines = {} # Key = texfile-path, value = [first line number the markup started, reconstructed latex code of marked text]
				had_hyphen = False
				for l in range(0, len(highlighted_pdflines)):
					# Get tex file and line number of this PDF line and remember it
					x = 0.5 * (annot.vertices[4*l][0] + annot.vertices[4*l+3][0]) # Centre of the marked area
					y = 0.5 * (annot.vertices[4*l][1] + annot.vertices[4*l+3][1])
					texfile, lineno = run_synctex(page.number, x, y, synctexfilename, synctexdir)
					if texfile not in highlighted_texlines:
						had_hyphen = True # Need to set this flag at the beginning of a new file otherwise space is added
						highlighted_texlines[texfile] = [lineno, ""]
						open_texfile(texfile, texfiles)
					#
					# Get highlighted text in PDF and add to existing texline, remove hyphen/add space if required
					highlighted = unicode2latex(highlighted_pdflines[l])
					if not had_hyphen: highlighted = " " + highlighted
					had_hyphen = False
					if highlighted[-1] == "-":
						highlighted = highlighted[:-1]
						had_hyphen = True
					#
					highlighted_texlines[texfile][1] += highlighted
				#


				# Iterate over files, add one \pdfmarkupcomment in each
				idx = {}
				for (texfile, (lineno, highlighted)) in highlighted_texlines.items():

					lineno -= 1
					highlighted = highlighted.split()
					texlines = texfiles[texfile]

					# Find the start
					w = 0
					i = 0
					j = 0
					texline = texlines[lineno]
					words = ""
					while j > -1 and w < len(highlighted):
						words = " ".join(highlighted[v] for v in range(w+1))
						i = j
						j = texline.find(words) # Need to use find here because word combinations matter
						w += 1
					#
					if j == -1: w -= 1 # Could not find word or ...
					else:       i = j  # .. no further words available in loop above
					idx[texfile] = [lineno, i, -1, -1]

					# Find stop
					# if not all words have been found and ???
					if w < len(highlighted): #and len(texline)-1 == i - 1 + sum(len(word)+1 for word in highlighted[:w]):
						i = 0
						lineno += 1
						texline = texlines[lineno]
						c = texline.find('%') # TODO function see above
						if c != -1: texline = texline[:c]
						while w < len(highlighted):
							if len(texline)-1 == i:
								i = 0
								while len(texline) <= 1:
									texlines[lineno] = '\\\\\\indent\n'
									lineno += 1
									texline = texlines[lineno]
									# TODO: could overflow index
								#
								texline = texlines[lineno]
								c = texline.find('%') # TODO function see above
								if c != -1: texline = texline[:c]
							#
							word = highlighted[w]
							if texline[i:i+len(word)] != word: warnings.warn('Word not matching \"%s\" (%s, %d)' % (word, texfile, lineno+1))
							i += len(word)+1
							w += 1
						#
						i -= 1
					#
					else: i += len(words)
					idx[texfile][2] = lineno
					idx[texfile][3] = i
				#
				print(idx, "\n\n")


				annot_tex = '\pdfmarkupcomment[id=%d,markup=%s,avatar={%s},date={%s},subject={ANNOT2TEX%s}]{' % (
					annot.xref,
					markup_types[annot.type[0]],
					authordict.get(annot.info['title'], 'ChuckNorris'),
					annot.info['modDate'],
					annot.info['id']
				)

				for texfile, j in idx.items():
					texlines = texfiles[texfile]
					# Start
					lineno = j[0]
					i = j[1]
					texlines[lineno] = texlines[lineno][:i] + annot_tex + texlines[lineno][i:]
					print(texlines[lineno])
					# Stop
					new_lineno = j[2]
					i = j[3] + (len(annot_tex) if new_lineno == lineno else 0)
					lineno = new_lineno
					texlines[lineno] = texlines[lineno][:i] + ('}{%s}' % annot.info['content']) + texlines[lineno][i:]
				#
			#
			else:
				raise Exception('Unknown annotation type %s' % annot.type[1])
			#
		#
	#
	doc.close()

	# Backup originals and write changes
	for texfile, texlines in texfiles.items():
		backup = texfile + '.bak'
		for l in texlines:
			print(l, end="")
		if os.path.exists(backup): raise Exception('Backup file exists, please clean that up first')
		shutil.copyfile(texfile, backup)
		f = open(texfile, 'w')
		f.writelines(texlines)
		f.close()
	#

	# TODO: check y coordinates of annots generated (and page), make this possible by adding an option alike -cmd='make main.pdf' and then analyse new pdf

	return
#





parser = argparse.ArgumentParser(
	prog='Sync into Tex',
	description='Extracts annotations from a PDF and places them at the correct location in that PDF\'s LaTex code'
)

# Need: pdf, directory containing tex and synctex files
parser.add_argument('pdf', help='Path to PDF file containing annotations')
parser.add_argument('synctex', help='Path to the synctex file')
parser.add_argument('root', help='Root path of the LaTex project of that PDF')
parser.add_argument('-b', '--buildcmd', help='command to build the PDF, which can be used to check the synchronised comments')
parser.add_argument('-a', '--authordict', help='YAML file containing a dictionary translating author names to pdfcomment.sty avatar names as defined in the tex project')
args = parser.parse_args()

# TODO: parse YAML authors

annot2tex(args.pdf, args.synctex, args.root, args.buildcmd, {})

