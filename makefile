.PHONY:start,all
all:
start:
	@echo "give me you aritcle name first"
	@while read newname;do \
		if [[ $${newname} == "" ]] ;then \
			echo "you entered a blank name, please try again";\
			echo "Or you can type Ctrl-C to quilt";\
		else \
			mkdir $${newname};\
			cp article_template/makefile $${newname};\
			touch $${newname}/$${newname}.markdown;\
			touch $${newname}/$${newname}.meta;\
			echo "It's ok to cd $${newname} to write ! have fun!";\
			break;\
		fi \
	done
