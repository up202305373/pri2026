.PHONY: all process stats clean

all: process stats

process:
	@echo "Running data processing pipeline..."
	python parser.py

stats:
	@echo "Generating corpus statistics..."
	python data_statistics.py

clean:
	@echo "Cleaning processed data..."
	rm -f data/processed/*.json data/processed/*.csv.gz