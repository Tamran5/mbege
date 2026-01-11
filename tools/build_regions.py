# tools/build_master_regions.py
import json
import requests
import os

def fetch_indonesia_regions():
    print("--- Memulai Pengambilan Master Data Wilayah Indonesia ---")
    
    # Sumber data: API publik wilayah Indonesia (emsifa/indonesia-geodata-api)
    base_url = "https://www.emsifa.com/api-wilayah-indonesia/api"
    
    try:
        # 1. Ambil Semua Provinsi
        print("Mengambil data Provinsi...")
        provinces_res = requests.get(f"{base_url}/provinces.json")
        provinces = provinces_res.json()
        
        master_data = {}

        for prov in provinces:
            prov_name = prov['name']
            prov_id = prov['id']
            master_data[prov_name] = {}
            print(f" > Memproses: {prov_name}")

            # 2. Ambil Kabupaten/Kota per Provinsi
            cities_res = requests.get(f"{base_url}/regencies/{prov_id}.json")
            cities = cities_res.json()

            for city in cities:
                city_name = city['name']
                city_id = city['id']
                master_data[prov_name][city_name] = []

                # 3. Ambil Kecamatan per Kabupaten/Kota
                districts_res = requests.get(f"{base_url}/districts/{city_id}.json")
                districts = districts_res.json()

                for dist in districts:
                    master_data[prov_name][city_name].append(dist['name'])

        # Simpan ke JSON
        output_file = 'regions_master.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=4)
            
        print(f"\nSelesai! File Master Wilayah berhasil dibuat: {os.path.abspath(output_file)}")
        print("Pindahkan file ini ke folder assets/data/ di proyek Flutter Anda.")

    except Exception as e:
        print(f"Terjadi kesalahan saat mengambil data: {str(e)}")

if __name__ == "__main__":
    fetch_indonesia_regions()