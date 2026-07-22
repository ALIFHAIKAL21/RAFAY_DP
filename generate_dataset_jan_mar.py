#!/usr/bin/env python3
"""
Generator Dataset Mentah Pesanan Logistik
Periode: Januari - Maret 2026
Target: 100 pasang (100 Induk + 100 Susulan = 200 header REQUEST ORDER)
Distribusi: Jan 20% (20 pasang), Feb 30% (30 pasang), Mar 50% (50 pasang)
Format mengikuti pola data_uji_demo (PESANAN_INDUK & PESANAN_SUSULAN)
"""

import random
from pathlib import Path

random.seed(2026)

BASE = Path(r"c:\Ngoding\Skripsi\IDP_RAFAY\Skripsi_rafay_IDP")
OUT = BASE / "DATASET JAN-MAR"

# ================================================================
# DATA POOLS (sesuai variasi di data_uji_demo)
# ================================================================

DRIVERS = [
    "Rifai","Aji","SENO","Supriyanto","Deden","Rasito","Sisno","Wandrianto",
    "Robbi","Ruspianto","Adhi","Yonal","Ferry","Beu","Sukur","Sutrisno",
    "M.Rizki","Agung","Endrik","Jatmiyanta","Purnama","Nana","Suryadi",
    "Andi","Danus","David","Aris","Andri","Saiful","Bagusti","Roni",
    "Akiyat","Wahyudi","M.Ibnu","Ruslan","Ardiansyah","Firman","Nur",
    "Hidayat","Anggoro","Mulyono","Teguh","Wawan","Cipto","Sutarman",
    "Yulianto","Sutris","Tomi","Aditya","Eko","Kardi","Paijo","Wahyu",
    "Irul","Juntak","Riyanto","Jabat","Marno","Toto","Gatot","Bayu",
    "Didik","Rudi","Abdullah","Yulizardi","Andika","Manulang","Jon",
    "Tedy","Sugeng","Chepy","Pariono","Ody","Tarto","Hanafi","Fauzi",
    "Galih","Bagus","Edi","Hombing","Joko","Cahyono","Yanto","Giat",
    "Rahmat","Indra","Arif","Arbi","Mayor","Nainggolan","Sapto","Parto",
    "Heri","Deni","Hendra","Bambang","Slamet","Gunawan","Santoso",
    "Hartono","Susilo","Budiman","Setiawan","Nugroho","Basuki","Purwanto",
    "Sudirman","Maulana","Hakim","Iskandar","Lukman","Fajar","Rizal",
    "Yusuf","Irwan","Hasan","Dedi","Budi","Cahyo","Sugiarto","Waluyo",
    "Supardi","Rusman","Darman","Karno","Poniman","Suyono","Tarno",
    "Warno","Samad","Parman","Jajang","Ujang","Asep","Dadang","Cecep",
    "Ridwan","Sahrul","Rohmat","Soleh","Iman","Suroto","Mulyadi",
    "Haryanto","Sutejo","Parjo","Tugimin","Sarno","Darto","Giono",
    "Misno","Karman","Daliman","Sumanto","Jumadi","Suyanto","Purwadi",
    "Warsito","Sunarto","Suharto","Suparjo","Tarmiji","Sodik","Rohim",
    "Zaenal","Kusnadi","Heriyanto","Drajat","Sofyan","Nurdin","Sulaiman",
    "Syamsul","Hamid","Rasyid","Mansur","Usman","Anwar","Kurniawan",
    "Surya","Darmawan","Prasetyo","Wibowo","M.Salim","A.Rahman",
    "Syahrul","Ilham","Fadli","Dimas","Yoga","Satria","Permana",
    "Febri","Gilang","Rian","Erwin","Hadi",
]

PLATE_PFX = ["B","F","L","BK","BM","BA","BE","BG","BH","AD","D","N","T","W"]
PLATE_SFX_LONG = [
    "TXA","TXW","UEU","UEW","UCK","SCP","SCD","SXW","TCP","FEV",
    "FXY","PCJ","KXW","KXV","UXZ","TXX","PXT","CXT","GBA","AMN",
]
PLATE_SFX_SHORT = [
    "FH","JM","UV","CO","VY","ES","FJ","EX","AU","RU","RO",
    "MH","GR","BC","OK","OG","OY","IP","H","UF","UE","AL",
    "UA","DJ","UR","UQ","FT","NF",
]

LOCATIONS = [
    "CIKARANG","MEGAHUB","CIKARANG + ARGOPANTES",
    "ANGKE POGLAR + ARGOPANTES","NGAWI",
    "MEGAHUB + ARGOPANTES","ARGOPANTES",
]

ROUTES = [
    "SUX - JEMBER","PML - PKL","PSR - PROBOLINGGO","MJK - MXG",
    "SRG - BTG","SUX - JBR","MDN - JBR","NEGARA - MENGWI",
    "MALANG - JBR","TGL - SUX",
]

TRUCKS = ["CDDL","TWB","WB"]

CAPS = ["24 /CBM","24 CBM","50 cbm","50 CBM","24 cbm","24cbm","",
        "50 /CBM","24/CBM","50/cbm"]

# Noise setelah header
NOISE_AFTER_HEADER = [
    "fyi pak ini dari pool, mohon dibantu monitor",
    "pak update unit sudah confirm dari vendor",
    "tolong bantu tarik dulu ya pak",
    "izin info tambahan dari gudang",
    "yang bawah masih nunggu kabar sopir",
    "noted pak, ini data masuk dari lapangan",
    "pak ini rombongan sudah koordinasi dengan pool",
    "sementara data sopir baru sebagian pak",
    "mohon dicatat dulu, no hp sudah aktif",
    "info dari admin, jadwal masih sesuai",
    "unit malam ini sudah siap loading",
    "data tambahan unit susulan sudah konfirm pak",
    "sisanya menyusul dari pool",
    "izin update data terbaru dari gudang",
    "berikut data unit yang sudah siap pak",
    "mohon bantu input data berikut",
    "ini data sementara dari lapangan pak",
    "sudah koordinasi dengan team gudang",
    "unit sudah standby di lokasi",
    "mohon diproses segera pak",
]

# Noise transisi (di susulan, sebelum unit tambahan)
TRANSITION_NOISE = [
    "berikut sisa data dari lapangan",
    "tambahan unit susulan sudah konfirm pak",
    "update data dari gudang",
    "ini sisa unit yang tadi",
    "mohon di lengkapi data berikut",
    "berikut tambahan sopir",
    "unit tambahan sudah siap",
    "TAMBAHAN DATA NYA",
    "update dari vendor",
    "berikut data sopir tambahan",
    "sisa unit sudah konfirm pak",
    "tambahan data unit berikut",
    "mohon ditambahkan data ini",
    "update sisa unit dari lapangan",
]

# ================================================================
# HEADER PATTERNS (dengan variasi typo)
# ================================================================

HEADER_INDUK = [
    "REQUEST ORDER ONCALL {d}",
    "REQUEST ORDER ONCALL {d}",
    "REQUEST ORDER ONCALL {d}",
    "REQUEST ORDER ONCALL {d}",
    "REQUESR ORDERR ONCAL {d}",
    "REQUEST ORDR ONCALL {d}",
    "REQUESTT ORDER ONCAL {d}",
    "REQUEST ORDR ON CALL {d}",
    "REQEST ORDER ONCALL {d}",
    "REQUER ORDER ONCALL {d}",
    "REQUEST ORDER ON CALL {d}",
]

HEADER_SUSULAN = [
    "REQUEST ORDER ULANG ONCALL {d}",
    "REQUEST ORDER ULANG ONCALL {d}",
    "REQUEST ORDER ULANG ONCALL {d}",
    "REQUEST ORDER ULANG ONCALL {d}",
    "REQUEST ORDER ULANGR ONCAL {d}",
    "REQEST ORDER ULANG ONCALL {d}",
    "REQUEST ORDER ULANG ON CALL {d}",
    "REQUESR ORDER ULANG ONCAL {d}",
    "REQUEST ORDR ULANG ONCALL {d}",
    "REQUER ORDER ULANG ONCALL {d}",
]

# ================================================================
# NAMA BULAN (variasi format)
# ================================================================

MF = {1: "JANUARI", 2: "FEBRUARI", 3: "MARET"}
MT = {1: "Januari", 2: "Februari", 3: "Maret"}
ML = {1: "januari", 2: "februari", 3: "maret"}
MS = {1: "JAN", 2: "FEB", 3: "MAR"}

# ================================================================
# LABEL STYLES (10 set label, mengikuti variasi di demo)
# ================================================================

LOC_LABELS = [
    "Lokasi : ", "Loksi : ", "Lokasi loading : ", "Pickup : ",
    "pICKUP : ", "LOKASI : ", "LOKASI PICKUP : ", "Lokasi pICKUP : ",
    "Lokasi pICKUP :", "LOKASI : ",
]
TIME_LABELS = [
    "Waktu loading : ", "tgl muat : ", "Waktu  : ", "Tgl Muaat : ",
    "Waktu mUAT : ", "Waktu LOADING : ", "Waktu lOADING : ",
    "lOADING : ", "Waktu LOADINGu  : ", "Waktu  : ",
]
ROUTE_LABELS = [
    "Rute : ", "Tujuan : ", "TUJUAN : ", "Rute/tujuan : ",
    "Rute/tujuan : ", "RUTE/TUJUAN : ", "Destinasi : ",
    "RUTE/TUJUAN : ", "Rute : ", "RUTE/TUJUAN : ",
]
DRIVER_LABELS = [
    "Drivr : ", "Nama : ", "DRIVER : ", "Driver : ",
    "nAMA Driver : ", "NAMA DRIVER : ", "Driverr : ",
    "DRIVER : ", "NAMA : ", "NAMA DRIVER : ",
]
PLATE_LABELS = [
    "Nopol : ", "Nopol : ", "No pOLISI : ", "Nopol : ",
    "No pOLISI : ", "Nopol : ", "Nop0l : ",
    "Nopol : ", "Nopol : ", "Nopol : ",
]
PHONE_LABELS = [
    "No hp : ", "No hp : ", "No tELPON : ", "No HP : ",
    "No tELPON : ", "No HP : ", "Hp : ",
    "No tLP : ", "No HP : ", "No HP : ",
]

HOURS = [
    "00:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00",
    "08:00", "09:00", "10:00", "11:00", "12:00", "14:00", "15:00",
    "16:00", "18:00", "20:00", "22:00", "23:00",
]


# ================================================================
# FUNGSI HELPER
# ================================================================

def format_date(day, month):
    """Format tanggal dengan variasi natural (seperti operator ketik)"""
    r = random.random()
    if r < 0.30:
        return f"{day:02d} {MF[month]} 2026"        # "05 JANUARI 2026"
    elif r < 0.50:
        return f"{day:02d} {MT[month]} 2026"         # "05 Januari 2026"
    elif r < 0.65:
        return f"{day:02d} {MT[month]} 26"           # "05 Januari 26"
    elif r < 0.75:
        return f"{day} {ML[month]} 26"               # "5 januari 26"
    elif r < 0.85:
        return f"{day} {MF[month]} 2026"             # "5 JANUARI 2026"
    else:
        return f"{day:02d} {MS[month]} 2026"         # "05 JAN 2026"


def gen_plate():
    """Generate plat nomor Indonesia realistis"""
    pfx = random.choice(PLATE_PFX)
    num = random.randint(8000, 9999)
    sfx = random.choice(PLATE_SFX_LONG) if random.random() < 0.55 else random.choice(PLATE_SFX_SHORT)
    return f"{pfx} {num} {sfx}"


def gen_phone():
    """Generate nomor HP Indonesia realistis (11-13 digit, +62, 628x)"""
    r = random.random()
    if r < 0.03:
        # +62 dengan dash
        return f"+62 {random.randint(811,899)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
    elif r < 0.06:
        # 628x tanpa +
        return f"628{random.randint(1,3)}{random.randint(100000000,999999999)}"
    elif r < 0.20:
        # 11 digit (08xxxxxxxx)
        px = random.choice(["081","082","083","085","087","088","089"])
        return f"{px}{random.randint(10000000,99999999)}"
    elif r < 0.38:
        # 13 digit (08xxxxxxxxxxxx)
        px = random.choice(["0881","0882","0859","0858","0857","0852"])
        return f"{px}{random.randint(100000000,999999999)}"
    else:
        # 12 digit (08xxxxxxxxx) - paling umum
        px = random.choice(["081","082","083","085","087","088","089"])
        return f"{px}{random.randint(100000000,999999999)}"


def gen_time(month=None, day=None, first_unit=False):
    """Generate waktu loading dengan variasi (titik, spasi, SEGERA, suffix tanggal)"""
    h = random.choice(HOURS)
    r = random.random()
    if r < 0.20:
        h = h.replace(":", ".")           # "12.00" (titik)
    elif r < 0.25:
        parts = h.split(":")
        if len(parts) == 2:
            h = f"{parts[0]}: {parts[1]}"  # "12: 00" (spasi setelah titik dua)
    # Suffix tanggal untuk unit pertama (rare)
    if first_unit and random.random() < 0.12 and month and day:
        next_day = min(day + 1, 28 if month == 2 else 31)
        h = f"{h} {next_day:02d}-{month:02d}-2026"
    # Sangat jarang: SEGERA
    if random.random() < 0.015:
        h = "SEGERA"
    return h


def gen_unit_line(total, truck):
    """Generate baris jumlah unit (variasi kapasitas & casing)"""
    cap = random.choice(CAPS)
    if random.random() < 0.15:
        t = truck.lower()
    elif random.random() < 0.08:
        t = truck.title()
    else:
        t = truck
    u = random.choice(["UNIT", "UNIT", "UNIT", "unit", "Unit"])
    line = f"{total} {u} {t}"
    if cap:
        line += f" {cap}"
    return line.rstrip()


# ================================================================
# FUNGSI UTAMA: GENERATE SATU PASANG (INDUK + SUSULAN)
# ================================================================

def generate_pair(day, month):
    """
    Menghasilkan satu pasang pesanan (Induk + Susulan).
    Mengembalikan tuple (induk_text, susulan_text).
    """
    date_str = format_date(day, month)
    total_units = random.randint(1, 8)

    # Tentukan berapa unit yang sudah terisi di Induk
    if total_units == 1:
        filled_count = 0            # 1 unit, semua kosong di induk
        show_empty_slots = True     # Tampilkan slot kosong
    else:
        filled_count = random.randint(1, total_units - 1)
        show_empty_slots = random.random() < 0.25  # 25% chance tampilkan slot kosong

    remaining_count = total_units - filled_count

    # Pilih atribut order
    location = random.choice(LOCATIONS)
    route = random.choice(ROUTES)
    truck = random.choice(TRUCKS)
    style_idx = random.randint(0, 9)
    noise_line = random.choice(NOISE_AFTER_HEADER)

    # Tracking driver unik per order
    used_drivers = set()

    def pick_driver():
        d = random.choice(DRIVERS)
        for _ in range(80):
            if d not in used_drivers:
                break
            d = random.choice(DRIVERS)
        used_drivers.add(d)
        return d

    # Generate data untuk SEMUA unit (agar waktu konsisten induk <-> susulan)
    all_units = []
    for i in range(total_units):
        all_units.append({
            "time": gen_time(month, day, first_unit=(i == 0)),
            "driver": pick_driver(),
            "plate": gen_plate(),
            "phone": gen_phone(),
        })

    filled_units = all_units[:filled_count]
    remaining_units = all_units[filled_count:]
    unit_line = gen_unit_line(total_units, truck)

    # ----------------------------------------------------------------
    # BUILD INDUK
    # ----------------------------------------------------------------
    ind = []
    ind.append(random.choice(HEADER_INDUK).format(d=date_str))
    ind.append(noise_line)
    ind.append(unit_line)
    ind.append(f"{LOC_LABELS[style_idx]}{location}")

    # Unit-unit yang sudah terisi
    for i, u in enumerate(filled_units):
        ind.append(f"{TIME_LABELS[style_idx]}{u['time']}")
        if i == 0 or random.random() < 0.45:
            ind.append(f"{ROUTE_LABELS[style_idx]}{route}")
        ind.append(f"{DRIVER_LABELS[style_idx]}{u['driver']}")
        ind.append(f"{PLATE_LABELS[style_idx]}{u['plate']}")
        ind.append(f"{PHONE_LABELS[style_idx]}{u['phone']}")

    # Slot kosong (jika ditampilkan)
    if show_empty_slots:
        for u in remaining_units:
            ind.append(f"{TIME_LABELS[style_idx]}{u['time']}")
            ind.append(DRIVER_LABELS[style_idx].rstrip())
            ind.append(PLATE_LABELS[style_idx].rstrip())
            ind.append(PHONE_LABELS[style_idx].rstrip())

    # ----------------------------------------------------------------
    # BUILD SUSULAN
    # ----------------------------------------------------------------
    sus = []
    sus.append(random.choice(HEADER_SUSULAN).format(d=date_str))
    sus.append(noise_line)
    sus.append(unit_line)
    sus.append(f"{LOC_LABELS[style_idx]}{location}")

    # Ulangi unit yang sudah terisi dari Induk (extra space pada label kadang-kadang)
    for i, u in enumerate(filled_units):
        sus.append(f"{TIME_LABELS[style_idx]}{u['time']}")
        if i == 0 or random.random() < 0.45:
            sus.append(f"{ROUTE_LABELS[style_idx]}{route}")
        drv_label = DRIVER_LABELS[style_idx]
        if random.random() < 0.3:
            drv_label = drv_label.replace(" :", "  :")
        sus.append(f"{drv_label}{u['driver']}")
        sus.append(f"{PLATE_LABELS[style_idx]}{u['plate']}")
        sus.append(f"{PHONE_LABELS[style_idx]}{u['phone']}")

    if show_empty_slots:
        # POLA A: Slot kosong diisi langsung (tanpa noise transisi)
        # Seperti di demo: induk ada placeholder kosong -> susulan mengisinya
        for u in remaining_units:
            sus.append(f"{TIME_LABELS[style_idx]}{u['time']}")
            drv_label = DRIVER_LABELS[style_idx]
            if random.random() < 0.4:
                drv_label = drv_label.replace(" :", "  :")
            sus.append(f"{drv_label}{u['driver']}")
            sus.append(f"{PLATE_LABELS[style_idx]}{u['plate']}")
            sus.append(f"{PHONE_LABELS[style_idx]}{u['phone']}")
    else:
        # POLA B: Noise transisi lalu unit tambahan
        # Seperti di demo: induk hanya menampilkan sebagian, susulan menambahkan sisanya
        sus.append(random.choice(TRANSITION_NOISE))
        for u in remaining_units:
            sus.append(f"Waktu loading  : {u['time']}")
            if random.random() < 0.55:
                sus.append(f"{ROUTE_LABELS[style_idx]}{route}")
            sus.append(f"Driver  : {u['driver']}")
            sus.append(f"Nopol : {u['plate']}")
            sus.append(f"No hp : {u['phone']}")

    return "\n".join(ind), "\n".join(sus)


# ================================================================
# MAIN
# ================================================================

def main():
    # Distribusi: Jan 20 pasang, Feb 30 pasang, Mar 50 pasang
    month_configs = [
        (1, 20, 31),   # Januari:  20 pasang, max 31 hari
        (2, 30, 28),   # Februari: 30 pasang, max 28 hari
        (3, 50, 31),   # Maret:    50 pasang, max 31 hari
    ]

    all_induk = []
    all_susulan = []

    for month_num, pair_count, max_days in month_configs:
        # Generate tanggal (diurutkan, boleh ada duplikat = beberapa order di hari sama)
        days = sorted(random.choices(range(1, max_days + 1), k=pair_count))
        for day in days:
            induk_text, susulan_text = generate_pair(day, month_num)
            all_induk.append(induk_text)
            all_susulan.append(susulan_text)

    # Buat folder output
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "PESANAN_INDUK").mkdir(parents=True, exist_ok=True)
    (OUT / "PESANAN_SUSULAN").mkdir(parents=True, exist_ok=True)

    # Tulis file
    induk_content = "\n".join(all_induk) + "\n"
    susulan_content = "\n".join(all_susulan) + "\n"
    combined_content = induk_content + susulan_content

    (OUT / "DATASET_MENTAH.TXT").write_text(combined_content, encoding="utf-8")
    (OUT / "PESANAN_INDUK" / "index.txt").write_text(induk_content, encoding="utf-8")
    (OUT / "PESANAN_SUSULAN" / "index.txt").write_text(susulan_content, encoding="utf-8")

    # Statistik
    total_pairs = len(all_induk)
    total_headers = total_pairs * 2
    total_lines = combined_content.count("\n")

    print(f"=" * 60)
    print(f"  DATASET GENERATOR - SELESAI")
    print(f"=" * 60)
    print(f"  Total pasang  : {total_pairs}")
    print(f"  Total header  : {total_headers} (REQUEST ORDER)")
    print(f"  Total baris   : {total_lines}")
    print(f"  Ukuran file   : {len(combined_content):,} bytes")
    print(f"=" * 60)
    print(f"  Output folder : {OUT}")
    print(f"  - DATASET_MENTAH.TXT")
    print(f"  - PESANAN_INDUK/index.txt")
    print(f"  - PESANAN_SUSULAN/index.txt")
    print(f"=" * 60)

    # Distribusi per bulan
    jan_count = 20
    feb_count = 30
    mar_count = 50
    print(f"\n  Distribusi:")
    print(f"    Januari  : {jan_count} pasang ({jan_count * 2} header)")
    print(f"    Februari : {feb_count} pasang ({feb_count * 2} header)")
    print(f"    Maret    : {mar_count} pasang ({mar_count * 2} header)")


if __name__ == "__main__":
    main()
