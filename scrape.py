import requests
import json

from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from os import environ

_ = environ.get

faskesEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes"
jadwalEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes/tanggal" # noqa E501
waktuEndpoint = "https://vaksinasi-corona.jakarta.go.id/service/api/faskes/waktu" # noqa E501
nominatimEndpoint = "https://nominatim.openstreetmap.org/search.php"
kuotaEndpoint = "https://jkt-vax-quota.vercel.app/api/kuota"
AUTHORIZATION_HEADER = "Bearer 2|1mcB0aYZjD4manNttOKyt5nE3PquT96yIDQYxofq"
JAKI_HEADER = {'Authorization': AUTHORIZATION_HEADER}
KUOTA_INTEGERATION_ENABLED = _("KUOTA_INTEGERATION_ENABLED", True)

s = requests.Session()
retries = Retry(total=30, backoff_factor=1, status_forcelist=[502, 503, 504])
s.mount('http://', HTTPAdapter(max_retries=retries))

if KUOTA_INTEGERATION_ENABLED:
    getKuota = s.get(kuotaEndpoint)
    if getKuota.status_code != 200:
        KUOTA_INTEGERATION_ENABLED = False
    else:
        dataKuota = getKuota.json()['data']

response = s.get(faskesEndpoint, headers=JAKI_HEADER, timeout=2)

if response.status_code != 200:
    print(f"error code {response.status_code}")
dataFaskes = response.json()
keyFaskes = [iFaskes['nama_lokasi_vaksinasi'] for iFaskes in dataFaskes]

for faskes in dataFaskes:
    getJadwal = s.get(jadwalEndpoint, params={
        'from_capil': False,
        'kode_lokasi_vaksinasi': faskes['kode_lokasi_vaksinasi']
    }, headers=JAKI_HEADER)
    faskes['jadwal'] = getJadwal.json()
    for jadwal in faskes['jadwal']:
        keyJadwal = [iJadwal['id'] for iJadwal in faskes['jadwal']]
        getWaktu = s.get(waktuEndpoint, params={
            'kode_lokasi_vaksinasi': jadwal['kode_lokasi_vaksinasi'],
            'tgl_kuota_vaksinasi': jadwal['id']
        }, headers=JAKI_HEADER)
        jadwal['waktu'] = getWaktu.json()

        if KUOTA_INTEGERATION_ENABLED:
            for waktu in jadwal['waktu']:
                keyWaktu = [iWaktu['id'] for iWaktu in jadwal['waktu']]
                keyKuota = f"{faskes['wilayah']}.{faskes['kecamatan']}." \
                    f"{faskes['kelurahan']}.{faskes['nama_lokasi_vaksinasi']}." \
                    f"{jadwal['id']}T{waktu['id']}.000Z"
                namaLokasi = faskes['nama_lokasi_vaksinasi']
                if keyKuota in dataKuota:
                    dataWaktu = {
                        "id": dataKuota[keyKuota]['jamKuota'],
                        "kuota": {
                            'totalKuota': dataKuota[keyKuota]['totalKuota'],
                            'sisaKuota': dataKuota[keyKuota]['sisaKuota'],
                            'jakiKuota': dataKuota[keyKuota]['jakiKuota'],
                        }
                    }
                    dataJadwal = {
                        "id": dataKuota[keyKuota]['tanggalKuota'],
                        "waktu": [dataWaktu]
                    }
                    waktu['kuota'] = {
                        'totalKuota': dataKuota[keyKuota]['totalKuota'],
                        'sisaKuota': dataKuota[keyKuota]['sisaKuota'],
                        'jakiKuota': dataKuota[keyKuota]['jakiKuota'],
                    }
                else:
                    if namaLokasi not in keyFaskes:
                        dataFaskes.append({
                            "nama_lokasi_vaksinasi": namaLokasi,
                            "wilayah": dataKuota[keyKuota]['wilayah'],
                            "kecamatan": dataKuota[keyKuota]['kecamatan'],
                            "kelurahan": dataKuota[keyKuota]['kelurahan'],
                            "jadwal": [dataJadwal],
                        })
                        keyFaskes.append(namaLokasi)
                        keyJadwal.append(dataKuota[keyKuota]['tanggalKuota'])
                        keyWaktu.append(dataKuota[keyKuota]['jamKuota'])

                    if dataKuota[keyKuota]['tanggalKuota'] not in keyJadwal:
                        faskes['jadwal'].append(dataJadwal)
                        keyJadwal.append(dataKuota[keyKuota]['tanggalKuota'])
                        keyWaktu.append(dataKuota[keyKuota]['jamKuota'])

                    if dataKuota[keyKuota]['jamKuota'] not in keyWaktu:
                        jadwal['waktu'].append(dataWaktu)
                        keyWaktu.append(dataKuota[keyKuota]['jamKuota'])
        else:
            for waktu in jadwal['waktu']:
                waktu['kuota'] = {}

    getLocation = s.get(nominatimEndpoint, params={
        'q': faskes['nama_lokasi_vaksinasi'],
        'format': 'jsonv2'
    })

    faskes['detail_lokasi'] = getLocation.json()
    faskes['last_updated_at'] = datetime.now().isoformat()

tmp = {}

for key, value in dataKuota.items():

    if value['namaLokasi'] not in tmp:
        tmp[value['namaLokasi']] = {
            "nama_lokasi_vaksinasi": value['namaLokasi'],
            "wilayah": value['wilayah'],
            "kecamatan": value['kecamatan'],
            "kelurahan": value['kelurahan'],
            "jadwal": {}
        }

    if value['tanggalKuota'] not in tmp[value['namaLokasi']]['jadwal']:
        tmp[value['namaLokasi']]['jadwal'][value['tanggalKuota']] = {
            "id": value['tanggalKuota'],
            "waktu": []
        }

    tmp[value['namaLokasi']]['jadwal'][value['tanggalKuota']]['waktu'].append({
        "id": value['jamKuota'],
        "kuota": {
            'totalKuota': value['totalKuota'],
            'sisaKuota': value['sisaKuota'],
            'jakiKuota': value['jakiKuota'],
        }
    })

for key, value in tmp.items():
    keyJadwal = []
    if key not in keyFaskes:
        getLocation = s.get(nominatimEndpoint, params={
            'q': faskes['nama_lokasi_vaksinasi'],
            'format': 'jsonv2'
        })

        dataFaskes.append({
            "nama_lokasi_vaksinasi": key,
            "wilayah": value['wilayah'],
            "kecamatan": value['kecamatan'],
            "kelurahan": value['kelurahan'],
            "jadwal": [],
            "detail_lokasi": getLocation.json(),
            "last_updated_at": datetime.now().isoformat()
        })
        keyFaskes.append(key)

        for jKey, jValue in value['jadwal'].items():
            iKey = keyFaskes.index(key)
            dataFaskes[iKey]['jadwal'].append({
                "id": jKey,
                "waktu": []
            })
            keyJadwal.append(jKey)

            for iWaktu in jValue['waktu']:
                wKey = keyJadwal.index(jKey)
                dataFaskes[iKey]['jadwal'][wKey]['waktu'].append(iWaktu)

        getLocation = s.get(nominatimEndpoint, params={
            'q': dataFaskes[iKey]['nama_lokasi_vaksinasi'],
            'format': 'jsonv2'
        })

        dataFaskes[iKey]['detail_lokasi'] = getLocation.json()
        dataFaskes[iKey]['last_updated_at'] = datetime.now().isoformat()


file_object = open(f'./jadwal.json', 'w+')
file_object.write(json.dumps(dataFaskes))
file_object = open(f'./daily_archive/'
                   f'{datetime.now().strftime("%Y-%m-%d")}.json', 'w+')
file_object.write(json.dumps(dataFaskes))
