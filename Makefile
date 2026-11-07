.PHONY: all process stats clean

all: process stats split solr-start solr-index-basic solr-index-improved

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

solr-start:
	sudo docker start pri_solr 2>/dev/null || docker run --name pri_solr -p 8983:8983 -d solr:10 solr-precreate games_basic
	sudo docker start pri_solr 2>/dev/null || docker run --name pri_solr -p 8983:8983 -d solr:10 solr-precreate games_improved

solr-index-basic:
	-sudo docker exec pri_solr solr delete -c games_basic
	sudo docker exec pri_solr solr create -c games_basic
	python3 milestone2/apply_schema.py games_basic milestone2/schema_basic.json
	python3 milestone2/prepare_solr.py
	for f in data/solr/games_batch_*.json; do curl --fail-with-body -s -X POST -H 'Content-Type: application/json' --data-binary @"$$f" http://localhost:8983/solr/games_basic/update || exit 1; done
	curl -s "http://localhost:8983/solr/games_basic/update?commit=true"

solr-index-improved:
	-sudo docker exec pri_solr solr delete -c games_improved
	sudo docker exec pri_solr solr create -c games_improved
	python3 milestone2/apply_schema.py games_improved milestone2/schema_improved.json
	for f in data/solr/games_batch_*.json; do curl --fail-with-body -s -X POST -H 'Content-Type: application/json' --data-binary @"$$f" http://localhost:8983/solr/games_improved/update || exit 1; done
	curl -s "http://localhost:8983/solr/games_improved/update?commit=true"

solr-count:
	@curl -s "http://localhost:8983/solr/games_basic/select?q=*:*&rows=0&fq=doc_type:game" | python3 -c "import json,sys; print('games:', json.load(sys.stdin)['response']['numFound'])"
	@curl -s "http://localhost:8983/solr/games_basic/select?q=*:*&rows=0&fq=doc_type:review" | python3 -c "import json,sys; print('reviews:', json.load(sys.stdin)['response']['numFound'])"
	@curl -s "http://localhost:8983/solr/games_improved/select?q=*:*&rows=0&fq=doc_type:game" | python3 -c "import json,sys; print('games:', json.load(sys.stdin)['response']['numFound'])"
	@curl -s "http://localhost:8983/solr/games_improved/select?q=*:*&rows=0&fq=doc_type:review" | python3 -c "import json,sys; print('reviews:', json.load(sys.stdin)['response']['numFound'])"

solr-stop:
	docker stop pri_solr