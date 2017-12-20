MARKDOWN_FILES:=user/GettingStarted.md

PDF_FILES:=$(patsubst %.md,%.pdf, $(MARKDOWN_FILES))

all: $(PDF_FILES)

$(PDF_FILES): %.pdf: %.md
	pandoc $*.md -s -o $@

clean:
	rm -f $(PDF_FILES)
	find -name "*~" -delete
