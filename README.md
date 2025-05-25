# ���z�����޲z�t��

## �M�׷��z

�o�O�@�Ӱ�� YOLOv7 �����˴������z�����޲z�t�ΡA�D�n�\��G
- **���������˴�**: �ϥ� YOLOv7 �ѧO�����P���P
- **������޲z**: �޲z 4 �Ӱ����쪺���α��p
- **���P����**: �۰ʿ��ѻP�O�����P���X
- **���O�p��**: �e30�����K�O�A�C�p��$20
- **API �A��**: ���� REST API �ѥ~�����Ψϥ�

## �t�ά[�c

```
���z�����޲z�t��
�u�w�w �˴��Ҳ� (����� + ��v��)
�x   �u�w�w detect_yolov7.py        # YOLOv7 �D�n�ʴ��{��
�x   �u�w�w detect_rec_plate.py     # ���P���ѵ{��
�x   �|�w�w weights/                # �V�m�n���ҫ��ɮ�
�x
�u�w�w API �A�ȼҲ�
�x   �u�w�w parking_api.py          # Flask API �D�{��
�x   �u�w�w requirements.txt        # �̿�M��C��
�x   �|�w�w .gitignore             # Git �����ɮ�
�x
�u�w�w ���դu��
�x   �u�w�w api_test.py            # ���� API �\��
�x   �u�w�w test_production.py     # �Ͳ����Ҵ���
�x   �|�w�w matplo_place.py        # �������mø�s
�x
�|�w�w ���p�ɮ�
    �u�w�w Procfile               # Render ���p�]�w
    �|�w�w render.yaml           # Render �t�m�ɮ�
```

---

## �ֳt�}�l���n

### �B�J 1: �ǳƶ}�o����

#### 1.1 �إߵ������� (Windows)
```bash
# �i�J�M�ץؿ�
cd "�A���M�׸��|"

# �إ߷s����������
python -m venv parking_env
parking_env\Scripts\activate
```

#### 1.2 �w�˩һݮM��
```bash
# �w�˩Ҧ����n�M��
pip install -r requirements.txt

# ���Ү֤߮M��w��
python -c "import torch, cv2, flask, numpy, shapely; print('�Ҧ��֤߮M��w�w�˦��\')"
```

#### 1.3 �ǳƼҫ��ɮ�
�T�O `weights/` ��Ƨ��]�t�G
- `best.pt` - YOLOv7 �����˴��ҫ�
- `yolov7_plate_0421.pt` - ���P���Ѽҫ�
- `new_pkg.p` - ������]�w�ɮ�

### �B�J 2: ���a���ըt��

#### 2.1 ���� YOLOv7 �˴��t��
```bash
# ���ը����˴� (�ϥ���v��)
python detect_yolov7.py --source 0 --weights weights/best.pt

# ���չϤ��ɮ��˴�
python detect_yolov7.py --source "test_image.jpg" --weights weights/best.pt
```

#### 2.2 ���ը��P���ѥ\��
```bash
# ���ը��P����
python detect_rec_plate.py --source "platePic" --weights weights/yolov7_plate_0421.pt
```

#### 2.3 �Ұ� API �A��
```bash
# �b���a�Ұ� API �A��
python parking_api.py
```

API �|�b `http://localhost:5000` ����A���ѥH�U���I�G
- `GET /` - �A�ȭ�����T
- `GET /health` - ���d�ˬd
- `POST /api/parking/update` - ��s�����쪬�A
- `GET /api/parking/status` - �d�ߩҦ�������
- `GET /api/parking/my_status?plate=���P` - �d�߭ӤH����

#### 2.4 ���� API �\��
```bash
# ����۰ʤƺ��I����
python api_test.py
```

### �B�J 3: ��X�t�δ���

#### 3.1 �s���˴��MAPI�t��
�b `detect_yolov7.py` ���w�t�m API �s���G

```python
# API �t�m - �i�H�q�L�����ܶq�]�mAPI�a�}
API_URL = os.environ.get('API_URL', 'https://parking-management-api-lyvg.onrender.com/api/parking/update')
```

#### 3.2 ����y�{����
```bash
# 1. �Ұ� API �A�� (�׺ݾ� 1)
python parking_api.py

# 2. �Ұ� YOLOv7 �˴� (�׺ݾ� 2)
python detect_yolov7.py --source 0

# 3. ���� API �\�� (�׺ݾ� 3)
python api_test.py
```

### �B�J 4: ���ݳ��p (Render)

#### 4.1 ���p�e�ǳ�

Render ���p�һ��ɮפw�ǳƦn�G
- `Procfile`: ���w�ҰʩR�O
- `.gitignore`: �ư������n���ɮ�

#### 4.2 �b Render �إ� PostgreSQL ��Ʈw

1. �n�J [Render.com](https://render.com)
2. �q�����ɯ��� "PostgreSQL"
3. �I�� "New PostgreSQL" �إ߷s��Ʈw
4. �t�m�]�w�G
   ```
   Name: parking-db
   Database: parking
   User: parking_user
   ```
5. �إ߫�A�O�U���Ѫ� "Internal Database URL" �M "External Database URL"

#### 4.3 ���p�� Render

1. �b Render ����x����� "Web Services"
2. �I�� "New Web Service"
3. �s���A�� GitHub �M��
4. �t�m���p�]�w�G
   ```
   Name: parking-management-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn parking_api:app
   ```
5. �b "Environment Variables" �]�w���A�K�[�G
   ```
   DATABASE_URL: [�q�W�@�B�ƻs�� Internal Database URL]
   ```
6. �I�� "Create Web Service" �Ұʳ��p

#### 4.4 ���ն��ݳ��p
```bash
# �ק�����ɮפ��� API ��¦�a�}
# �N API_BASE_URL �����ܼƳ]�w���A�� Render ���}
export API_BASE_URL="https://�A������.onrender.com/api"
python api_test.py
```

### �B�J 5: ������]�m

#### 5.1 ������t�m
�b������W�ק� `detect_yolov7.py`�A�]�w���� API�G

```python
# �]�w API ���}
API_URL = "https://�A������.onrender.com/api/parking/update"
```

#### 5.2 �]�w�۰ʱҰ�
�إ� `start_detection.sh`�G
```bash
#!/bin/bash
cd /home/pi/parking_project
source venv/bin/activate
python detect_yolov7.py --source 0
```

�]�w���}���۰ʰ���G
```bash
# �s�� crontab
crontab -e

# �[�J�H�U��
@reboot /home/pi/parking_project/start_detection.sh
```

---

## API �ϥλ���

### ��¦URL
- **���a�}�o**: `http://localhost:5000/api`
- **�Ͳ�����**: `https://parking-management-api-lyvg.onrender.com/api`

### �D�n���I

#### 1. ��s�����쪬�A (������ϥ�)
```http
POST /api/parking/update
Content-Type: application/json

[
  {"ID": 1, "IsOccupied": true, "LicensePlateNumber": "ABC-1234"},
  {"ID": 2, "IsOccupied": false, "LicensePlateNumber": "None"},
  {"ID": 3, "IsOccupied": false, "LicensePlateNumber": "None"},
  {"ID": 4, "IsOccupied": false, "LicensePlateNumber": "None"}
]
```

#### 2. �d�߰��������A
```http
GET /api/parking/status
```

�^���d�ҡG
```json
[
  {"id": 1, "is_occupied": true, "plate_number": "ABC-1234"},
  {"id": 2, "is_occupied": false, "plate_number": null},
  {"id": 3, "is_occupied": false, "plate_number": null},
  {"id": 4, "is_occupied": false, "plate_number": null}
]
```

#### 3. �d�߭ӤH�������A
```http
GET /api/parking/my_status?plate=ABC-1234
```

�^���d�ҡG
```json
{
  "is_parked": true,
  "parking_slot": 1,
  "started_at": "2023-05-24 14:00:00",
  "duration_minutes": 85,
  "fee": 20
}
```

## ��Ʈw����

### PostgreSQL ��Ʈw�[�c

���t�Ψϥ� PostgreSQL ��Ʈw�s�x������T�A�D�n��ƪ��c�G

```sql
CREATE TABLE parking_spaces (
    id INTEGER PRIMARY KEY,
    is_occupied BOOLEAN DEFAULT FALSE,
    license_plate_number VARCHAR(20),
    license_plate_color VARCHAR(20),
    parking_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### ��Ʈw�s���]�w

- �t�γz�L�����ܼ� `DATABASE_URL` �۰ʳs���� Render ���Ѫ� PostgreSQL ��Ʈw
- �p�G�����ܼƤ��s�b�A�t�η|�۰ʤ�����O����Ҧ��B�@
- �O����Ҧ��A�X���a�}�o�M����

### �ʱ���Ʈw���A

�i�q�L���d�ˬd���I�ʱ���Ʈw�s�����A�G

```http
GET /health
```

�^���d�ҡG
```json
{
  "status": "healthy",
  "timestamp": "2023-05-24T14:00:00",
  "uptime": "running",
  "database": "connected"
}
```

## �i���}�o��ĳ

### 1. ��Ʈw�X�i
- �W�[ PostgreSQL �e�q
- �]�p���v�O����
- �إߥΤ�{��

### 2. �e�ݶ}�o
- React.js �޲z����
- �Y�ɨ������
- ��� App ��X

### 3. �\��ݮi
- ���P�w���\��
- ���������馩
- �h�إI�ڤ覡

---

## ���D�Ƹ�

�p�G�J����D�A���ˬd�G
1. �����ܼƳ]�w�O�_���T (`DATABASE_URL` �M `API_URL`)
2. �Ҧ��̿�M��O�_�w�w��
3. �ҫ��ɮ׬O�_�w��m�󥿽T��m
4. �T�O�����s������X�� API �A��
5. Render �A�Ȫ��A�O�_���`�B�@

### �`�����D�ѨM���

#### ��Ʈw�s�����~
```
? ��Ʈw�s������: �s���Q�ڵ�
```
�ѨM��סG�ˬd `DATABASE_URL` �O�_���T�A�νT�{ Render PostgreSQL �A�ȬO�_�b�B�椤

#### API �s�����D
```
? �L�k�s���� API �A��
```
�ѨM��סG�ˬd�����s���A�T�{ API �A�Ⱥ��}�O�_���T�ARender �A�ȬO�_�Ұ�

#### ���P���Ѱ��D
```
���P���ѿ��~: [Error]
```
�ѨM��סG�T�{ `weights/` ��Ƨ������ҫ��ɮ׬O�_����A�ˬd��v���s���M���u����

---

## ���v����

���M�׶ȨѾǲ߻P��s�ϥΡA�ФťΩ�ӷ~�ت��C

---

*�̫��s: 2023�~5��24��*