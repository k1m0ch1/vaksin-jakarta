import requests
import json

from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from os import environ

_ = environ.get

faskesEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes"
jadwalEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes/tanggal"
waktuEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes/waktu"
nominatimEndpoint = "https://nominatim.openstreetmap.org/search.php"
kuotaEndpoint = "https://jkt-vax-quota.vercel.app/api/kuota"
AUTHORIZATION_HEADER = "Bearer 2|1mcB0aYZjD4manNttOKyt5nE3PquT96yIDQYxofq"
KUOTA_INTEGERATION_ENABLED = _("KUOTA_INTEGERATION_ENABLED", False)

s = requests.Session()
retries = Retry(total=30, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
s.mount('http://', HTTPAdapter(max_retries=retries))

if KUOTA_INTEGERATION_ENABLED:
    getKuota = s.get(kuotaEndpoint)
    if getKuota.status_code != 200:
        KUOTA_INTEGERATION_ENABLED = False
    else:
        dataKuota = getKuota.json()['data']

response = s.get(faskesEndpoint, headers={'Authorization': AUTHORIZATION_HEADER}, timeout=2)

if response.status_code != 200:
    print(f"error code {response.status_code}")
dataFaskes = response.json()

for faskes in dataFaskes:
    getJadwal = s.get(jadwalEndpoint, params= {
        'from_capil': False,
        'kode_lokasi_vaksinasi': faskes['kode_lokasi_vaksinasi']
    }, headers={'Authorization': AUTHORIZATION_HEADER})
    faskes['jadwal'] = getJadwal.json()
    for jadwal in faskes['jadwal']:
        getWaktu = s.get(waktuEndpoint, params= {
            'kode_lokasi_vaksinasi': jadwal['kode_lokasi_vaksinasi'],
            'tgl_kuota_vaksinasi': jadwal['id']
        }, headers={'Authorization': AUTHORIZATION_HEADER})
        jadwal['waktu'] = getWaktu.json()

        if KUOTA_INTEGERATION_ENABLED:
            for waktu in jadwal['waktu']:
                keyKuota = f"{faskes['wilayah']}.{faskes['kecamatan']}.{faskes['kelurahan']}.{faskes['nama_lokasi_vaksinasi']}.{jadwal['id']}.{waktu['id']}"
                if keyKuota in dataKuota:
                    waktu['kuota'] = {
                        'totalKuota': dataKuota[keyKuota]['totalKuota'],
                        'sisaKuota': dataKuota[keyKuota]['sisaKuota'],
                        'jakiKuota': dataKuota[keyKuota]['jakiKuota'],
                    }
                else:
                    waktu['kuota'] = {}

    getLocation = s.get(nominatimEndpoint, params= {
        'q': faskes['nama_lokasi_vaksinasi'],
        'format': 'jsonv2'
    })

    faskes['detail_lokasi'] = getLocation.json()
    faskes['last_updated_at'] = datetime.now().isoformat()

file_object = open(f'./jadwal.json', 'w+')
file_object.write(json.dumps(dataFaskes))