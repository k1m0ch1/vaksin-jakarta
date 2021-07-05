import requests
import json

from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

faskesEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes"
jadwalEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes/tanggal"
waktuEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes/waktu"
nominatimEndpoint = "https://nominatim.openstreetmap.org/search.php"

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
    for jadwal in faskes['jadwal']:
        getWaktu = s.get(waktuEndpoint, params= {
            'kode_lokasi_vaksinasi': jadwal['kode_lokasi_vaksinasi'],
            'tgl_kuota_vaksinasi': jadwal['id']
        })
        jadwal['waktu'] = getWaktu.json()

    getLocation = s.get(nominatimEndpoint, params= {
        'q': faskes['nama_lokasi_vaksinasi'],
        'format': 'jsonv2'
    })

    faskes['detail_lokasi'] = getLocation.json()
    faskes['last_updated_at'] = datetime.now().isoformat()
        

file_object = open(f'./jadwal.json', 'w+')
file_object.write(json.dumps(dataFaskes))