import json

with open('d:/Study/DH/IoT in 5G/detection_anomaly/detection_anomaly/model_development/retrain-model-FINAL-OPTIMIZED.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'markdown' and 'Feature Engineering' in ''.join(cell['source']):
        cell['source'] = ['## 2. (Skipped) Feature Engineering\n', 'Sử dụng đúng 24 features gốc như bài báo, không thêm feature phái sinh.']
    elif cell['cell_type'] == 'code' and 'df[\'BytesRatio\']' in ''.join(cell['source']):
        cell['source'] = [
            '# Move Label to last temporarily\n',
            'column_to_move = df.pop(\'Label\')\n\n',
            '# Put Label back\n',
            'df[\'Label\'] = column_to_move\n\n',
            'feature_names = df.columns[:-1].tolist()\n',
            'print(f"✓ Using {len(feature_names)} features")'
        ]

with open('d:/Study/DH/IoT in 5G/detection_anomaly/detection_anomaly/model_development/retrain-model-FINAL-OPTIMIZED.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
