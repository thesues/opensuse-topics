MARKDOWNSRC=$(wildcard *.markdown)
TOP := $(shell basename `pwd`)
TARGET=$(patsubst %,%.pdf,${TOP})
TEXSRC=$(patsubst %,%.tex,${TOP})
#SRC=$(wildcard *.tex)
SVNVERSION=$(shell git log --pretty=oneline |wc -l )
PDFTARGET=$(patsubst %.pdf,%-r${SVNVERSION}.pdf,${TARGET})
title=$(shell sed -n "s/\\\title{\(.*\)}/\1/p" ${TEXSRC})

.PHONY:clean html download view blog latex tex start
all:${TARGET}
clean:
	rm -rf *.pdf
	rm -rf *.out
	rm -rf *.log
	rm -rf *.toc
	rm -rf *.aux

tex:${TEXSRC}
latex:${TEXSRC}
%.pdf:%.tex %.toc
	xelatex  $< 
%.toc:%.tex
	xelatex  $<
%.tex:%.markdown %.meta
	../maketex.py $<
${PDFTARGET}:${TARGET}
	cp $< ${PDFTARGET}

#TODO to use markdown file to html insdead of latex
html:${TEXSRC}
	latex2html -local_icons -html_version 4.0,latin1,unicode $<
blog:${TEXSRC}
	latex2html -lcase_tags -mkdir -dir blog -split 0 -nonavigation -noinfo -html_version 4.0,latin1,unicode $<
publish:${PDFTARGET}
	@echo "now publish $< to code.google.com..."
	@echo "please make sure you have googlecode_upload.py in your path!"
	@echo "If you DON'T have googlecode_upload.py,Download from http://code.google.com/support"
	@echo "wget http://support.googlecode.com/svn/trunk/scripts/googlecode_upload.py"
	../googlecode_upload.py  -s "${title}" -p opensuse-topics $<
view:${PDFTARGET}
	evince $<&
