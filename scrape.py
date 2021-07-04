import requests
import json

from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

faskesEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes";
jadwalEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes/tanggal";

start = datetime.now()
s = requests.Session()
retries = Retry(total=30, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
s.mount('http://', HTTPAdapter(max_retries=retries))

response = s.get(faskesEndpoint, timeout=2)
dataFaskes = response.json()

for faskes in dataFaskes:
    getJadwal = s.get(jadwalEndpoint, params= {
        'from_capil': False,
        'kode_lokasi_vaksinasi': faskes['kode_lokasi_vaksinasi']
    })
    faskes['jadwal'] = getJadwal.json()

file_object = open(f'./jadwal.json', 'w+')
file_object.write(json.dumps(dataFaskes))