"""
Run a suite of produce images through the YOLO grading function and record results.
This script imports `analyze_produce_with_yolo` from `main.py` (which loads the model)
and evaluates a set of sample images downloaded from public URLs.

Outputs:
 - prints per-image grading
 - writes `grading_results.csv` and `grading_results.json` in `backend/tests/`

Run with: python tests/run_yolo_grading_tests.py
"""

import os
import time
import json
import csv
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image
import sys
from pathlib import Path as _Path

# Ensure project root is on sys.path so we can import main
project_root = _Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import grading function from main (this will also attempt to load the YOLO model)
from main import analyze_produce_with_yolo

# Create test images directory
BASE_DIR = Path(__file__).parent
IMG_DIR = BASE_DIR / 'grading_images'
IMG_DIR.mkdir(exist_ok=True)

# A curated list of 20 sample produce image queries (Unsplash source). These return
# public images matching the query and are resilient to hotlinking if a User-Agent
# header is provided.
IMAGE_URLS = [
    # Tomatoes
    'https://upload.wikimedia.org/wikipedia/commons/8/87/Tomatoes_on_the_vine.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/7/7b/Peeled_tomatoes.jpg',
    # Apples
    'https://upload.wikimedia.org/wikipedia/commons/1/15/Red_Apple.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/8/88/Apples.jpg',
    # Carrots
    'https://upload.wikimedia.org/wikipedia/commons/7/74/Carrots.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/4/49/Carrot_bundle.jpg',
    # Potatoes
    'https://upload.wikimedia.org/wikipedia/commons/6/60/Background_potatoes.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/5/5f/Potatoes.jpg',
    # Bananas
    'https://upload.wikimedia.org/wikipedia/commons/4/4c/Bananas.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/8/8a/Bananas_(2).jpg',
    # Onions
    'https://upload.wikimedia.org/wikipedia/commons/4/43/Onions.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/1/10/Red_onions.jpg',
    # Eggplant
    'https://upload.wikimedia.org/wikipedia/commons/6/69/Aubergines.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/4/49/Eggplant.jpg',
    # Chillies
    'https://upload.wikimedia.org/wikipedia/commons/3/39/Red_Chilli_Pepper.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/8/8c/Chili_Peppers.jpg',
    # Cucumbers
    'https://upload.wikimedia.org/wikipedia/commons/0/02/Cucumber.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/9/95/Cucumbers.jpg',
    # Mixed produce (market pile)
    'https://upload.wikimedia.org/wikipedia/commons/3/35/Various_vegetables.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/9/9b/Vegetables_on_market.jpg'
]

results = []

for idx, url in enumerate(IMAGE_URLS, start=1):
    print(f"[{idx}/{len(IMAGE_URLS)}] Downloading: {url}")
    try:
        # Use a browser-like User-Agent and set Referer for Wikimedia to avoid 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://commons.wikimedia.org'
        }
        r = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert('RGB')
        # Save a copy locally for reference
        fname = IMG_DIR / f'image_{idx:02d}.jpg'
        img.save(fname)

        # Run grading
        t0 = time.time()
        grading = analyze_produce_with_yolo(img, produce_title=f"Image {idx}")
        t1 = time.time()
        elapsed = t1 - t0

        record = {
            'index': idx,
            'url': url,
            'local_path': str(fname),
            'grade': grading.get('grade'),
            'price_range': grading.get('price_range'),
            'analysis': grading.get('analysis'),
            'time_seconds': round(elapsed, 3)
        }
        results.append(record)
        print(f" -> Grade: {record['grade']}, time: {record['time_seconds']}s")
    except Exception as e:
        print(f"Error processing {url}: {e}")
        results.append({'index': idx, 'url': url, 'error': str(e)})

# Write results to CSV and JSON
csv_path = BASE_DIR / 'grading_results.csv'
json_path = BASE_DIR / 'grading_results.json'

with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['index', 'url', 'local_path', 'grade', 'price_range', 'analysis', 'time_seconds', 'error']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        row = {k: r.get(k, '') for k in fieldnames}
        writer.writerow(row)

with open(json_path, 'w', encoding='utf-8') as jf:
    json.dump(results, jf, indent=2, ensure_ascii=False)

print('\nDone. Results written to:')
print(f' - {csv_path}')
print(f' - {json_path}')
print('Sample outputs:')
for r in results:
    print(f"{r.get('index')}: {r.get('grade')} - {r.get('price_range')} ({r.get('time_seconds', '')}s) {('\n  ' + r.get('analysis')) if r.get('analysis') else ''}")
