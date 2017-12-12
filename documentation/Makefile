MARKDOWN_FILES:=user/GettingStarted.md

PDF_FILES:=$(patsubst %.md,%.pdf, $(MARKDOWN_FILES))

all: $(PDF_FILES)

$(PDF_FILES): %.pdf: %.md
	gimli -f $*.md -o $(dir $@)

clean:
	rm -f $(PDF_FILES)
	find -name "*~" -delete
