#!/usr/bin/python
import os
import sys
import os.path
import pdb

if len(sys.argv) < 2:
    print "Please specify a markdown file"
    print "exiting..."
    sys.exit(-1)
dir_name=os.path.dirname(sys.argv[1])
base_name=os.path.basename(sys.argv[1])
main_name=os.path.splitext(base_name)[0]

cmd="pandoc -fmarkdown -tlatex %s" % sys.argv[1]
tex_content=os.popen(cmd).read()
#to do some filter stuff
tex_content=tex_content.replace("begin{enumerate}[1.]","begin{enumerate}")
#read meta data

metafile=os.path.join(dir_name,main_name+".meta");

meta_header=""
if os.path.exists(metafile):
    title=""
    author=""
    date=""
#     pdb.set_trace()
    for line in open(metafile,"r"):
        segs=line.split("=");
        if segs[0] == "title":
            title = segs[1].strip()
        if segs[0] == "author":
            author = segs[1].strip()
        if segs[0] == "date":
            date == segs[1].strip()
    meta_header="\\title{%s}\n\\author{%s}\n\\date{%s}\n" % (title, author, date)
else:
    print "hey, you have not a meta file to indicate who you are and the title for your article"

header=\
"\input{../header}\n"\
"\\begin{document}\n"\
"%s"\
"\maketitle\n"\
"\\tableofcontents\n"\
"\\newpage" % meta_header;

foot=\
"\input{../readme}\n"\
"\end{document}"

#combine togeter
main_tex="%s\n%s\n%s" % (header,tex_content,foot)

f=open(os.path.join(dir_name,main_name+".tex"),"w")
f.write(main_tex);


