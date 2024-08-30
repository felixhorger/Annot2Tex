# Annot2Tex

Extract PDF annotations (which can be added by most PDF viewers) and insert them into LaTex code.
This is useful if you want to keep the review history, while continuing to modify your LaTex code.

If you 

- find this useful please leave a star
- find bugs file an issue
- think this is roughly what you need but not exactly let me know
- want to improve it or collaborate don't hesitate, ask

Shoutout to

- Jorj X. McKie (@[JorjMcKie](https://www.github.com/JorjMcKie)) and the devs of `pymupdf`
- Philippe Faist (@[phfaist](https://www.github.com/phfaist)) and the devs of `pylatexenc`
- Jerome Laurens for developing `synctex`
- Josef Kleber for developing `pdfcomment.sty`
- Ulrike Fischer (@[u-fischer](https://www.github.com/u-fischer)) for providing solutions to some problems `pdfcomment.sty` has [here](https://tex.stackexchange.com/a/694614)
- ThV for doing the same [here](https://tex.stackexchange.com/a/408976)

Big thanks that your work and help made this possible!



## Installation

### Requirements
I used `python3` version `3.9.2` and the following packages
```
pylatexenc==2.10
PyMuPDF==1.24.9
PyYAML==5.3.1
```
but I'm sure it does work too if you don't have these exact versions.


### Annot2Tex
```
git clone https://github.com/felixhorger/Annot2Tex.git
cd Annot2Tex
make install
```


## Usage

### Prepare your LaTex project
#### 1. Add this to the preamble
```
\usepackage{pdfcomment.sty}
\makeatletter
\renewcommand*{\pc@get@PDFOBJID}[1]%
 {%
  \zref@extractdefault{#1}{PCPDFOBJID}{S,0}%
 }%
\makeatother
\makeatletter \AtEndDocument{\immediate\write\@auxout{\string\ulp@afterend}} \makeatother
```

#### 2. Define authors in Tex
`pdfcomment.sty` calls them avatars, e.g.
```
\defineavatar{Felix}{author=Felix, color=cyan}
\defineavatar{Chuck}{author=Chuck, color=orange}
```

#### 3. Define authors in `YAML`
Mapping from author names in the PDF annotations (this could be e.g. the windows user name)
to the avatar names defined above. If you don't provide this mapping the names will be used as they are in the PDF.

#### 4. Add synctex
In the final compilation step add `-synctex=1` to the cmdline args of `pdflatex`, which generates the required synctex file.

### Add annotations using PDF viewer
I only tested this with the free version of the Adobe Acrobat Reader (version 2024.003.20054).
Not every type of annotation works yet.
Currently simple comment boxes and markup comments are supported as well as replies.

### Before you run `annot2tex`

> [!CAUTION]
> **I'm not responsible for any lost data**.
> This tool is in development and testing is restricted to my own use cases.
> I recommend that you track your LaTex files with `git`, commiting and pushing all changes _before_ running `annot2tex`.
> On top of that, to minimise risk, `annot2tex` automatically copies files (to `*.bak`) before changes are applied.
> If you try to run `annot2tex` while these backup files are still around, it won't apply changes and throw an exception asking you to remove them
> to acknowledge that the tex code is in a consistent state.
> So, should you be worried or refrain from using `annot2tex`? No.
> But be alert, and make use of `git diff` to ensure that `annot2tex` did what it was supposed to.

### Run

Have a look at the cmdline help via

```annot2tex```

everything should be in there, if it's unclear please let me know.


