.PHONY: all process stats clean

all: process stats

process:
	@echo "Running data processing pipeline..."
	python3 milestone1/parser.py

stats:
	@echo "Generating corpus statistics..."
	python3 milestone1/data_statistics.py

clean:
	@echo "Cleaning processed data..."
	rm -f data/processed/*.json data/processed/*.csv.gz data/processed/analysis_output_*.txt

split:
	@echo "Splitting dataset into 3 parts..."
	python3 milestone1/splitter.py