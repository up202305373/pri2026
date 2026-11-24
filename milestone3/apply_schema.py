import json, subprocess, sys

core, schema_path = sys.argv[1], sys.argv[2]
URL = f"http://localhost:8983/solr/{core}/schema"
data = json.load(open(schema_path))
commands = data if isinstance(data, list) else [data]

for entry in commands:
    for command, body in entry.items():
        payload = json.dumps({command: body})
        r = subprocess.run(["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
                            "--data-binary", payload, URL], capture_output=True, text=True)
        print(body["name"], r.stdout.strip()[:150])