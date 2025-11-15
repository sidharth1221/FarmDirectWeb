"""
Run YOLO grading on all local images in `tests/grading_images/`.
Place the attached images into that folder (jpg/png). Then run this script.
Outputs:
 - tests/local_grading_results.csv
 - tests/local_grading_results.json

Run with: python tests/run_yolo_on_local_images.py
"""

import sys
from pathlib import Path
import time
import json
import csv
from PIL import Image

# Ensure project root on path
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from main import analyze_produce_with_yolo
except Exception as e:
    print("Error importing analyze_produce_with_yolo from main:", e)
    raise

BASE_DIR = Path(__file__).parent
IMG_DIR = BASE_DIR / 'grading_images'
IMG_DIR.mkdir(exist_ok=True)

image_files = sorted([p for p in IMG_DIR.iterdir() if p.suffix.lower() in ['.jpg', '.jpeg', '.png']])
if not image_files:
    print(f"No local images found in {IMG_DIR}. Please save the attachments there and re-run.")
    sys.exit(0)

results = []
for idx, img_path in enumerate(image_files, start=1):
    print(f"[{idx}/{len(image_files)}] Processing: {img_path.name}")
    try:
        img = Image.open(img_path).convert('RGB')
        t0 = time.time()
        grading = analyze_produce_with_yolo(img, produce_title=str(img_path.name))
        t1 = time.time()
        elapsed = t1 - t0
        record = {
            'filename': str(img_path.name),
            'grade': grading.get('grade'),
            'price_range': grading.get('price_range'),
            'analysis': grading.get('analysis'),
            'time_seconds': round(elapsed, 3)
        }
        results.append(record)
        print(f" -> {record['filename']}: Grade={record['grade']}, time={record['time_seconds']}s")
    except Exception as e:
        print(f"Error processing {img_path.name}: {e}")
        results.append({'filename': str(img_path.name), 'error': str(e)})

csv_path = BASE_DIR / 'local_grading_results.csv'
json_path = BASE_DIR / 'local_grading_results.json'

with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['filename', 'grade', 'price_range', 'analysis', 'time_seconds', 'error']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        row = {k: r.get(k, '') for k in fieldnames}
        writer.writerow(row)

with open(json_path, 'w', encoding='utf-8') as jf:
    json.dump(results, jf, indent=2, ensure_ascii=False)

print('\nDone. Results written to:')
print(' -', csv_path)
print(' -', json_path)
