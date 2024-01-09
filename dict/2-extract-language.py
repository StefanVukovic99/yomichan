import json
import fileinput
import os

output = []

source_iso = os.environ.get("source_iso")
source_language = os.environ.get("source_language")
target_iso = os.environ.get("target_iso")

line_count = 0  # Initialize a line counter
print_interval = 1000  # Set the interval for progress updates

inputFile = f"data/kaikki/{source_iso}-extract.json"
print(f"Reading {inputFile}...")

for line in fileinput.input(inputFile, openhook=fileinput.hook_encoded("utf-8")):
    object = json.loads(line)
    if("lang_code" not in object):
        if("redirect" not in object):
            print(f"Error: no lang_code or redirect in line {line_count}.", object)
        continue
    if object["lang_code"] == source_iso:
        output.append(line.strip())

    line_count += 1  # Increment the line counter

    # Print progress at the specified interval
    if line_count % print_interval == 0:
        print(f"Processed {line_count} lines...", end="\r")

print("Finished reading raw-wiktextract-data.json.")

print(f"Writing {source_iso}-{target_iso}-extract.json...", len(output))

with open(f"data/kaikki/{source_iso}-{target_iso}-extract.json", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("Finished.")
