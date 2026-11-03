import json, subprocess

URL = "http://localhost:8983/solr/games/schema"
data = json.load(open("milestone2/schema_fix.json"))
commands = data if isinstance(data, list) else [data]

for entry in commands:
    for command, body in entry.items():
        payload = json.dumps({command: body})
        r = subprocess.run(["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
                            "--data-binary", payload, URL], capture_output=True, text=True)
        print(body["name"], r.stdout.strip()[:150])