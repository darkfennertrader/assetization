.PHONY: pdf clean

# Build the research PDF
pdf:
	bash docs/build-pdf.sh

clean:
	rm -f docs/agent-assetization-research.pdf docs/build.log
