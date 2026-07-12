# generate_paired.py
# Script untuk menghasilkan dataset pasangan induk-susulan Feb-Mar 2026
# Sesuai aturan:
# 1. Pesanan induk mendahului susulan
# 2. Urutan antar pasangan dicampur (tidak blok terpisah)
# 3. Typo & noise dipertahankan
# 4. Susulan = copy pelengkap dari induk + data tambahan

output_lines = []

def add(text):
    output_lines.append(text)

# ============================================================
# 01 FEBRUARI 2026
# ============================================================
add("""[05:31, 07/03/2026] Akbar Rafay: Request Unit On Call Tgl 01 FEB 2026

RAFAY

1 UNIT TWB 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - MES
driver  : Samosir
Nopol  : B 9727 UEax
No hp  :+62 822-7429-6236
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST  ORDER ONCALL 01 FEBUARI 2025

RAFAY

2 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU
driver  : Fery Alfit
Nopol  : BM 8734 AU
No hp  : 082364441218

Waktu loading : segera
Rute/tujuan : CGK - PKU
driver  :
Nopol  :
No hp :

Data yang lain menyusul
""")

# SUSULAN 01 FEBRUARI (langsung setelah induknya)
add("""REQUEST ULANG ORDER ONCALL 01 FEBUARI 2025

RAFAY

2 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU
driver  : Fery Alfit
Nopol  : BM 8734 AU
No hp  : 082364441218

Waktu loading : segera
Rute/tujuan : CGK - PKU
driver  : RYAN
Nopol  : B 9084 VEH
No hp  : 087837496810

Data yang lain menyusul
""")

# ============================================================
# 02 FEBRUARI 2026 - induk berbagai tipe
# ============================================================
add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST  ORDER ONCALL 02 FEBRUARI 2026


1 unit tronton 50 cbm
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : *CGK - mes
driver  : Sormin
Nopol  : BK 8927 XE
No hp  : 0821 7529  4978
""")

add("""[05:31, 07/03/2026] Akbar Rafay: Request Unit On Call Tgl 02 Feb 26

RAFAY

1 Unit Tronton/50 Cbm
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK- MES 
driver  : Supriadi
Nopol  : BK 8994 XH
No hp  : 081375534124
""")

# Susulan 02 Feb (MES)
add("""REQUEST ULANG ORDER ONCALL 02 FEBRUARI 2026

1 unit tronton 50 cbm
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : *CGK - mes
driver  : Sormin
Nopol  : BK 8927 XE
No hp  : 0821 7529  4978

REQUEST ULANG ORDER ONCALL Tgl 02 Feb 26

RAFAY

1 Unit Tronton/50 Cbm
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK- MES 
driver  : Supriadi
Nopol  : BK 8994 XH
No hp  : 081375534124
""")

add("""[05:31, 07/03/2026] Akbar Rafay: Request Unit On Call Tgl 02 Feb 26

RAFAY

1 Unit Tronton/50 Cbm
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK- PKU 
driver  : Dafit Hidayat
Nopol  : BM 8725 AU
No hp  : 081266608055
""")

# Susulan 02 Feb (PKU)
add("""REQUEST ULANG ORDER ONCALL Tgl 02 Feb 26

RAFAY

1 Unit Tronton/50 Cbm
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK- PKU 
driver  : Dafit Hidayat
Nopol  : BM 8725 AU
No hp  : 081266608055
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST  ORDER ONCALL 02 FEBRUARI 2025:

RAFAY

1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : SEGERA
Rute/tujuan : CGK - JATENG
driver  :Rajiev Fikri
Nopol  :B 9479 UXZ
No hp  : 0882-9029-4126
""")

# Susulan 02 Feb JATENG
add("""REQUEST ULNG ORDER ONCALL 02 FEBRUARI 2025:

RAFAY

1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : SEGERA
Rute/tujuan : CGK - JATENG
driver  :Rajiev Fikri
Nopol  :B 9479 UXZ
No hp  : 0882-9029-4126
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST  ORDER ONCALL 02 FEBRUARI 2026:


4 unit Cddl 24 Cbm
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - JATIM TENTATIF

waktu loading : 20:00
Nama  : AwAn Setiawan 
Nopol : B 9036 BXT
No hp :  081317133316

5* unit Cddl 24 Cbm
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - JATENG TENTATIF 

waktu loading : 20:00
Nama:Riski
Nopol:B 9189 TXR
No hp:085719586455

waktu loading : 20:00
Nama Susanto
Hp +62 812-3327-5955
No pol B9122PXR
""")

# Susulan 02 Feb (multi unit - tambahan driver baru)
add("""REQUESTT ULANG ORDER ONCALL 02 FEBRUARI 2026:

4 unit Cddl 24 Cbm
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - JATIM TENTATIF

waktu loading : 20:00
Nama  : AwAn Setiawan 
Nopol : B 9036 BXT
No hp :  081317133316

5* unit Cddl 24 Cbm
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - JATENG TENTATIF 

waktu loading : 20:00
Nama:Riski
Nopol:B 9189 TXR
No hp:085719586455

waktu loading : 20:00
Nama Susanto
Hp +62 812-3327-5955
No pol B9122PXR

waktu loading : 21:00
Nama  : HENDRA S.P
Nopol : D 9044 AG
No hp : +62 877-8667-6177
""")

# ============================================================
# 03 FEBRUARI 2026
# ============================================================
add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ONCALL 03 FEBRUARI 2026:

RAFAY
2 unit cdll 24 CBM 
Lokasi argo pantes cikokol 
Rute / tujuan : cgk - Jatim tentatif
Waktu loading : segera
driver  : Adin
Nopol  : B 9592 UXX
No hp  : 083852157054
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST  ULANG ORDER ONCALL DAN TAMBAHAN 03 FEBRUARI 2026

RAFAY

2 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : 01:00
Rute/tujuan : CGK- MES
driver  : Suhendi
Nopol  : L 8845 UT
No hp  : 083112495598
""")

# Susulan 03 Feb (gabung induk MES+JATIM)
add("""REQUEST ORDER ULNG DAN TAMBAHAN 03 FEBRUARI 2026

RAFAY

2 unit cdll 24 CBM 
Lokasi argo pantes cikokol 
Rute / tujuan : cgk - Jatim tentatif
Waktu loading : segera
driver  : Adin
Nopol  : B 9592 UXX
No hp  : 083852157054

2 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : 01:00
Rute/tujuan : CGK- MES
driver  : Suhendi
Nopol  : L 8845 UT
No hp  : 083112495598
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ONCALL 03 FEBRUARI 2026:

3 unit cddl 24 CBM 
Lokasi argo pantes cikokol 
Rute / tujuan :cgk - Jateng tentatif 
Waktu loading :segera

RAFAY
Driver : DEDEN
Nopol : E 9073 HB
No telp : 085717341340

""")

# Susulan 03 Feb JATENG (tambah driver AKIYAT)
add("""REQUEST ULANG ORDER ONCALL 03 FEBRUARI 2026:

3 unit cddl 24 CBM 
Lokasi argo pantes cikokol 
Rute / tujuan :cgk - Jateng tentatif 
Waktu loading :segera

RAFAY
Driver : DEDEN
Nopol : E 9073 HB
No telp : 085717341340

Driver : AKIYAT
Nopol : L 9722 UE
No telp :081281122738
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST  ULANG ORDER ONCALL DAN TAMBAHAN 03 FEBRUARI 2026

RAFAY
2 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : 01:00
Rute/tujuan : CGK- PKU
driver  : ENDRA
Nopol  :L 8791 UK
No hp  :081210911369
""")

add("""[05:31, 07/03/2026] Akbar Rafay: Request Unit On Call

1 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : segera

RAFAY
Rute/tujuan : CGK- SUB
driver  : M. syaichoni
Nopol  : N 8827 RK
No hp  :+62 812-3189-5971
""")

# Susulan PKU (tambah M. Rizki)
add("""REQUEST ULANG ORDER ONCALL DAN TAMBAHAN 03 FEBRUARI 2026

RAFAY
2 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : 01:00
Rute/tujuan : CGK- PKU
driver  : ENDRA
Nopol  :L 8791 UK
No hp  :081210911369

driver  : M. Rizki
Nopol  : BM 9156 RU
No hp  : 082255315151
""")

# Susulan SUB (ganti M.Syaichoni -> Yuda)
add("""REQUEST ULANG ORDER ONCALL Tgl 03 Feb

RAFAY

1 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : segera
Rute/tujuan : CGK- SUB
driver  : Yuda
Nopol  : W 8973 UQ
No hp  : 089507296985

Note : Pak @Unknown user Pak @Unknown user 

Penggangti M. Syaichoni
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST  ULANG ORDER ONCALL DAN TAMBAHAN 03 FEBRUARI 2026

RAFAY
2 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : 01:00
Rute/tujuan : CGK- PKU
driver  : M. Rizki
Nopol  : BM 9156 RU
No hp  : 082255315151
""")

# ============================================================
# 04 FEBRUARI 2026
# ============================================================
add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST TAMBAHAN ORDER ONCALL 04 FEBRUARI 2026:

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB

RAFAY
driver  : JAMAADI
Nopol  : L 8786 BN
No hp  :082229973792
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST TAMBAHAN ORDER ONCALL 04 FEBRUARI 2026:

RAFAY
2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU
driver  :IKRARDINATA
Nopol  :BM 9184 AU
No hp  :085371842600
""")

# Susulan 04 Feb tambahan SUB+PKU digabung
add("""REQUEST TAMBAHAN ORDER ULNG ONCALL 04 FEBRUARI 2026:

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB

RAFAY
driver  : JAMAADI
Nopol  : L 8786 BN
No hp  :082229973792

driver  : AGUS
Nopol  : D 9713 AF
No hp  :08817021866
""")

add("""REQUEST TAMBAHAN ORDER ULANG ONCALL 04 FEBRUARI 2026:

RAFAY
2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU
driver  :IKRARDINATA
Nopol  :BM 9184 AU
No hp  :085371842600

driver  :Redi Hadianto
Nopol  :BM 8365 AU
No hp  :085282259835
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST TAMBAHAN ORDER ONCALL 04 FEBRUARI 2026:

RAFAY
2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU
driver  :Redi Hadianto
Nopol  :BM 8365 AU
No hp  :085282259835
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST TAMBAHAN ORDER ONCALL 04 FEBRUARI 2026:

RAFAY
2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : AGUS
Nopol  : D 9713 AF
No hp  :08817021866
""")

# Rev plat (susulan AGUS)
add("""REQUEST TAMBAHAN ORDER ULNG ONCALL 04 FEBRUARI 2026:

RAFAY
2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : AGUS
Nopol  : D 9667 AF
No hp  :08817021866

Rev plat nomor pak @Unknown user @Unknown user @Unknown user \U0001f64f\U0001f3fb
""")

add("""[05:31, 07/03/2026] Akbar Rafay: Request Unit On Call

RAFAY
1 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : segera
Rute/tujuan : CGK- PDG
driver  : SUTRISNO
Nopol  : BM 8364 AU
No hp  :0853-5388-6066
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ONCALL 04 FEBRUARI 2026:

RAFAY
3 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : segera
Rute/tujuan : CGK - JATENG
driver  : KARYADI
Nopol  : AD 8517 BA
No hp  :085865762797
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ONCALL 04 FEBRUARI 2026:
RAFAY
1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : segera
Rute/tujuan : CGK - DPS
driver 1 : Edi setiawan
No hp  :0881023544597 
Driver2 : Jatmiyanta
No hp  :082118558105
Nopol : F 9647 FH
""")

# Susulan 04 Feb - berbagai unit
add("""REQUEST ULANG ORDER ONCALL 04 FEBRUARI 2026:

RAFAY
1 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : segera
Rute/tujuan : CGK- PDG
driver  : SUTRISNO
Nopol  : BM 8364 AU
No hp  :0853-5388-6066
""")

add("""REQUEST ULANG ORDER ONCALL 04 FEBRUARI 2026:

RAFAY
3 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : segera
Rute/tujuan : CGK - JATENG
driver  : KARYADI
Nopol  : AD 8517 BA
No hp  :085865762797
""")

add("""REQUEST ULANG ORDER ONCALL 04 FEBRUARI 2026:

RAFAY
1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : segera
Rute/tujuan : CGK - DPS
driver 1 : Edi setiawan
No hp  :0881023544597 
Driver2 : Jatmiyanta
No hp  :082118558105
Nopol : F 9647 FH
""")

# ============================================================
# SUSULAN 04 Feb - REQUEST ORDER ULANG ONCALL (5 unit SUB)
# ============================================================
add("""REQUEST ORDER ULANG ONCALL

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  :
Nopol  :
No hp  :

Waktu loading : 18:00
Rute/tujuan : CGK - SUB
driver  : m syaichoni
Nopol  : N 8872 Rk
No hp  : +62 812-3189-5971

Waktu loading : 21:00
Rute/tujuan : CGK - SUB
driver  :
Nopol  :
No hp  :

Waktu loading : 00:00
Rute/tujuan : CGK - SUB
driver  :
Nopol  :
No hp  :

Waktu loading : 03:00 05/02/2026
Rute/tujuan : CGK -SUB
driver  : Lailan
Nopol  : S 9272 UP
No hp  : +62 878-8686-1780
""")

# ============================================================
# 05 FEBRUARI 2026
# ============================================================
add("""REQUEST ULANG ORDER ONCALL 05 FEBRUARI 2026:

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - TKG
driver  :
Nopol  :
No hp  :

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PLM
driver  :
Nopol  :
No hp  :

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU
driver  : Siswanto
Nopol  : B 9120 WXR
No hp  : 081943564062

Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU
driver  : 
Nopol  : 
No hp  : 

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - MES
driver  : feri irawan
Nopol  : BK 8516 VV
No hp  : 085219216210
""")

add("""REQUEST ULANG ORDER ONCALL 05 FEBRUARI 2026:
RAFAY
2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - MES
driver  : HADI
Nopol  :B 9446 MV
No hp  :+62 831-9621-8655
""")

add("""REQUEST ULANG ORDER ONCALL 05 FEBRUARI 2026:
RAFAY
2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - MES
driver  : A. Sukur 
Nopol  :B 9477 KEU
No hp  : 083169525183
""")

add("""REQUEST ULANG ORDER ONCALL

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
RAFAY
driver  : AKIYAT
Nopol  : L 9722 UE
No hp  :081281122738
""")

add("""REQUEST ULANG ORDER ONCALL 05 FEBRUARI 2025
RAFAY
2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU
driver  : RYAN
Nopol  : B 9084 VEH
No hp  : 087837496810
""")

add("""REQUEST ULANG ORDER ONCALL 05 FEBRUARI 2026:

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PLM
driver  : SANDRI
Nopol  : BE 9636 BU
No hp  :+62 889-0702-0037
""")

# Susulan gabungan 05 Feb (lengkap semua driver MES)
add("""REQUEST ULNG DAN TAMBAHAN ORDER ONCALL 05 FEBRUARI 2026:

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - TKG
driver  :
Nopol  :
No hp  :

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PLM
driver  : SANDRI
Nopol  : BE 9636 BU
No hp  :+62 889-0702-0037

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU
driver  : Siswanto
Nopol  : B 9120 WXR
No hp  : 081943564062

Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU
driver  : RYAN
Nopol  : B 9084 VEH
No hp  : 087837496810

2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - MES
driver  : feri irawan
Nopol  : BK 8516 VV
No hp  : 085219216210

driver  : HADI
Nopol  :B 9446 MV
No hp  :+62 831-9621-8655

driver  : A. Sukur 
Nopol  :B 9477 KEU
No hp  : 083169525183
""")

add("""Request Unit On Call Tgl 05 Feb 26

2 Unit  Cddl / 24 Cbm
Lokasi : Cikarang
Waktu loading : 06:00/ 06-02-26
Rute/tujuan : CKR-Jateng Tentative
Driver   : 
Nopol  : 
No Hp  :

1 Unit  Cddl / 24 Cbm
Lokasi : Cikarang
Waktu loading : 03:00/ 06-02-26
Rute/tujuan : CKR-Jateng Tentative
Nama : Apar Rahmat 
Nopol : E9406HB 
NO TLP : 085971812879
""")

# ============================================================
# 06 FEBRUARI 2026
# ============================================================
add("""Request Unit On Call Tgl 06 febuary 2026

RAFAY
3 unit twb 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA 
Rute/tujuan : CGK- Jl.perak surabaya-PT.BM
driver  : M. iBNU
Nopol  : L 9511 AL
No hp  :082191633212
""")

add("""Request Unit On Call Tgl 06 febuary 2026


2 unit twb 50 CBM
Lokasi : JNE SUB
Waktu loading : SEGERA 
Rute/tujuan : SUB-CGK
driver  : WAHYUDI
Nopol  : N 9549 UA
No hp  :085784422398
""")

add("""Request Unit On Call Tgl 06 febuary 2026


2 unit twb 50 CBM
Lokasi : JNE SUB
Waktu loading : SEGERA 
Rute/tujuan : SUB-CGK
driver  : SOFYAN
Nopol  : B 9679 WT
No hp  : 082231837381
""")

# Susulan 06 Feb gabung 3 unit SUB
add("""REQUEST ULANG ORDER ONCALL Tgl 06 Feb 26

RAFAY
3 unit twb 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA 
Rute/tujuan : CGK- Jl.perak surabaya-PT.BM
driver  : M. iBNU
Nopol  : L 9511 AL
No hp  :082191633212

driver  : WAHYUDI
Nopol  : N 9549 UA
No hp  :085784422398

driver  : SOFYAN
Nopol  : B 9679 WT
No hp  : 082231837381
""")

add("""REQUEST ORDER ULANG ONCALL
06 FEB 2026

6 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 07:00 07-02-2026*
Rute/tujuan : CGK - SUB
driver  : Chandra
Nopol  : L 8601 UH
No hp  : +62 852-3168-1470
""")

add("""REQUEST ORDER ULANG ONCALL
06 FEB 2026

10 UNIT CDDL/24 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - JATIM TENTATIF

REVISI DRIVER
driver  : UMAR ALI
Nopol  : B 9932 SXW
No hp  :+62 858-9308-0799
""")

# Susulan 06 Feb gabungan 6+10 unit
add("""REQUEST ORDER ULNG ONCALL
06 FEB 2026

6 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 07:00 07-02-2026*
Rute/tujuan : CGK - SUB
driver  : Chandra
Nopol  : L 8601 UH
No hp  : +62 852-3168-1470

10 UNIT CDDL/24 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - JATIM TENTATIF
driver  : UMAR ALI
Nopol  : B 9932 SXW
No hp  :+62 858-9308-0799
""")

add("""REQUEST ORDER ONCAL
06 FEBUARI 2026

RAFAY
3 unit TWB 50 Cbm
Lokasi : ARGOPANTES
Rute/ tuj : CGK - MES
Waktu loading : SEGERA
DRIVER 1 : SENTOT
NOPOL    : B 9231 CEU
NOHP      :+62 812-8714-7789
""")

add("""REQUEST ORDER ONCAL
06 FEBUARI 2026

5 unit TWB 50 Cbm
Lokasi : ARGOPANTES
Rute/ tuj : CGK - SUB
Waktu loading : SEGERA
RAFAY
DRIVER 1 : PURWANTO
NOPOL    : B 9891 BEU
NOHP      :083142142113
""")

add("""REQUEST ORDER ONCAL
06 FEBUARI 2026

5 unit TWB 50 Cbm
Lokasi : ARGOPANTES
Rute/ tuj : CGK - SUB
Waktu loading : SEGERA
DRIVER : DIDIK
NOPOL    : B 9687 JM
NOHP      :085385220743
""")

add("""REQUEST ORDER ONCAL
06 FEBUARI 2026
Lokasi : ARGOPANTES
Rute/ tuj : CGK - PKU
Waktu loading : segera
DRIVER 1 : Haryono
NOPOL    : B 8745 AMR
NO HP      : 083166684195
""")

add("""REQUEST ORDER ONCAL
06 FEBUARI 2026

5 unit TWB 50 Cbm
Lokasi : ARGOPANTES
Rute/ tuj : CGK - SUB
Waktu loading : SEGERA
DRIVER : HERMANTO
NOPOL : S 8635 NJ
NOHP :085194592825
""")

# Susulan 06 Feb - SUB gabungan 3 driver
add("""REQUEST ULANG ORDER ONCAL
06 FEBUARI 2026

RAFAY
3 unit TWB 50 Cbm
Lokasi : ARGOPANTES
Rute/ tuj : CGK - MES
Waktu loading : SEGERA
DRIVER 1 : SENTOT
NOPOL    : B 9231 CEU
NOHP      :+62 812-8714-7789
""")

add("""REQUEST ULANG ORDER ONCAL
06 FEBUARI 2026

5 unit TWB 50 Cbm
Lokasi : ARGOPANTES
Rute/ tuj : CGK - SUB
Waktu loading : SEGERA
RAFAY
DRIVER 1 : PURWANTO
NOPOL    : B 9891 BEU
NOHP      :083142142113

DRIVER : DIDIK
NOPOL    : B 9687 JM
NOHP      :085385220743

DRIVER : HERMANTO
NOPOL : S 8635 NJ
NOHP :085194592825
""")

add("""REQUEST ULANG ORDER ONCAL
06 FEBUARI 2026
Lokasi : ARGOPANTES
Rute/ tuj : CGK - PKU
Waktu loading : segera
DRIVER 1 : Haryono
NOPOL    : B 8745 AMR
NO HP      : 083166684195
""")

# ============================================================
# 07-08 FEBRUARI 2026
# ============================================================
add("""REQUEST ORDER ONCAL
07 FEBUARI 2026
RAFAY
1 unit CDDL 24 Cbm
Lokasi : SEMARANG
Rute/ tuj : SRG - SUB
Waktu loading : SEGERA
DRIVER 1 :Agung
DRIVER 2 :Wijaya
NOPOL    :H 9948 RA
NOHP      :0882016641381
""")

add("""REQUEST ULANG ORDER ONCAL
07 FEBUARI 2026
RAFAY
1 unit CDDL 24 Cbm
Lokasi : SEMARANG
Rute/ tuj : SRG - SUB
Waktu loading : SEGERA
DRIVER 1 :Agung
DRIVER 2 :Wijaya
NOPOL    :H 9948 RA
NOHP      :0882016641381
""")

add("""REQUEST ORDER ONCALL 08 FEBRUARI 2025:

3 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - MES
driver  : DARMAWAN
Nopol  : BA 8829 BU
No hp  :082363564665
""")

# Susulan 08 Feb (tambah Suhendi)
add("""REQUEST ULANG ORDER ONCALL 08 FEBRUARI 2025:

3 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - MES
driver  : DARMAWAN
Nopol  : BA 8829 BU
No hp  :082363564665

driver  : Suhendi
Nopol  : L 8845 UT
No hp  : 083112495598
""")

# ============================================================
# 09 FEBRUARI 2026
# ============================================================
add("""Request Order Oncall Tgl 09 Feb

1 UNIT CDDL 24 CBM
Lokasi  : JNE SRG
Waktu loading  : 22.00
Rute/tujuan : SRG-CGK
Driver : Arif R
Nopol :B 9787 XX
No hp :089690885555
""")

add("""REQUEST ORDER  ONCALL 9 FEBRUARI 2026:

2 unit TWB 50 Cbm
Lokasi : cikokol
Waktu loading : 02:00 10/02/2026
Rute/tujuan : CGK - SUB
NAMA : WAHYUDI
NOPOL: N 9549 UA
NO HP :085784422398

Waktu loading : 03:00 10/02/2026
NAMA : YUDA
NOPOL: W 8973 UQ
NO HP :089507296985
""")

add("""REQUEST ORDER  ONCALL 9 FEBRUARI 2026:


2 unit  TWB 50 Cbm
Lokasi : Cikokol
Waktu loading : 02:00 10/02/2026
Rute/tujuan : CGK - PKU
NAMA : ALDI
NOPOL: BM 8350 AU
NO HP :0831-6761-0479

Waktu loading : 03:00 10/02/2026
NAMA :
NOPOL:
NO HP :
""")

add("""Request Order Oncall Tgl 09 Feb

1 UNIT CDDL 24 CBM
Lokasi  : JNE SRG
Waktu loading  : 02.00/10-02-26
Rute/tujuan : SRG-CGK
Driver : Supriadi
Nopol : B 9586 TXV
No hp :081350529712
""")

add("""REQUEST ORDER  ONCALL 9 FEBRUARI 2026:


2 unit  TWB 50 Cbm
Lokasi : Cikokol
Waktu loading : 02:00 10/02/2026
Rute/tujuan : CGK - PKU
Waktu loading : 03:00 10/02/2026
NAMA : SYAFRIZAL
NOPOL: BM 8479 AU
NO HP :082170733190
""")

add("""REQUEST ORDER  ONCALL 9 FEBRUARI 2026:

RAFAY
2 unit  TWB 50 Cbm
Lokasi : Cikokol
Rute/tujuan : CGK - PKU
Waktu loading :Segera
NAMA : SYAFRIZAL
NOPOL: BM 8479 AU
NO HP :082170733190
""")

# Susulan 09 Feb gabungan SRG
add("""REQUEST ULANG ORDER ONCALL Tgl 09 Feb

1 UNIT CDDL 24 CBM
Lokasi  : JNE SRG
Waktu loading  : 22.00
Rute/tujuan : SRG-CGK
Driver : Arif R
Nopol :B 9787 XX
No hp :089690885555

Waktu loading  : 02.00/10-02-26
Driver : Supriadi
Nopol : B 9586 TXV
No hp :081350529712
""")

# Susulan 09 Feb SUB + PKU
add("""REQUEST ULANG ORDER  ONCALL 9 FEBRUARI 2026:

2 unit TWB 50 Cbm
Lokasi : cikokol
Waktu loading : 02:00 10/02/2026
Rute/tujuan : CGK - SUB
NAMA : WAHYUDI
NOPOL: N 9549 UA
NO HP :085784422398

Waktu loading : 03:00 10/02/2026
NAMA : YUDA
NOPOL: W 8973 UQ
NO HP :089507296985
""")

add("""REQUEST ULANG ORDER  ONCALL 9 FEBRUARI 2026:

2 unit  TWB 50 Cbm
Lokasi : Cikokol
Waktu loading : 02:00 10/02/2026
Rute/tujuan : CGK - PKU
NAMA : ALDI
NOPOL: BM 8350 AU
NO HP :0831-6761-0479

Waktu loading : 03:00 10/02/2026
NAMA : SYAFRIZAL
NOPOL: BM 8479 AU
NO HP :082170733190
""")

# ============================================================
# 11-12 FEBRUARI 2026
# ============================================================
add("""REQUEST ORDER ONCALL 11 FEBRUARI 2026:



1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 00.00
Rute/tujuan : CGK - DPS
driver  :Nizar
Nopol  :B 9172 SCP
No hp  :081313444015
""")

add("""REQUEST ORDER ONCALL 11 FEBRUARI 2026:

3 unit tronton 50 Cbm
Lokasi : cikokol
Waktu loading : segera
Rute/tujuan : CGK - MES
Waktu loading : 09:00
Driver : SAMOSIR
Nopol : B 9727 UEX
Hp :+62 822-7429-6236

Waktu loading : 12:00
Driver : JONI
Nopol : B 9169 UEX
Hp :+62 822-7638-5077
""")

# Susulan 11 Feb DPS
add("""REQUEST ULANG ORDER ONCALL 11 FEBRUARI 2026:

1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 00.00
Rute/tujuan : CGK - DPS
driver  :Nizar
Nopol  :B 9172 SCP
No hp  :081313444015
""")

# Susulan 11 Feb MES (tambah 1 driver lagi)
add("""REQUEST ULANG ORDER ONCALL 11 FEBRUARI 2026:

3 unit tronton 50 Cbm
Lokasi : cikokol
Waktu loading : segera
Rute/tujuan : CGK - MES

Waktu loading : 09:00
Driver : SAMOSIR
Nopol : B 9727 UEX
Hp :+62 822-7429-6236

Waktu loading : 12:00
Driver : JONI
Nopol : B 9169 UEX
Hp :+62 822-7638-5077

Waktu loading : 14:00
Driver : DARMAWAN
Nopol : BA 8829 BU
No hp  :082363564665
""")

add("""REQUEST ORDER TAMBAHAN ONCALL  12 FEBRUARI 2026:

1 unit TRONTON 50 Cbm
Lokasi : cikokol
Waktu loading : 02:00  12/02/2026
Rute/tujuan : CGK - PKU
Nama \t: NASIP K
Nopol\t\t: BH 8165 QI
No Tlp\t\t:\u200a+6281272463920
""")

add("""Request Unit On Call Tgl 12 Feb 26

1 Unit  TWB 50 Cbm
Lokasi : Cikarang
Waktu loading : Segera
Rute/tujuan : CKR-SUB-SUX 
Driver   : AGENG
Nopol  : B9654YU
No Hp  : +62 857-0738-0584
""")

add("""Request Unit On Call Tgl 12 Feb 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/ 13-02-26
Rute/tujuan : CGK-JBR
No pol.   : F 9647 FH
Driver. 1 :  Jatmiyanta
No hp :  : 082118558105
Driver 2  : Ilham Wahyudi
No hp.    : 089519041791
""")

add("""REQUEST ORDER ONCALL 12 FEBRUARI 2026:
RAFAY
3 unit tronton 50 Cbm
Lokasi : cikokol
Waktu loading : segera
Rute/tujuan : CGK - MES
driver  : SRI MARDONO
Nopol  : BK 8678 VE
No hp  :085218843366
""")

add("""REQUEST ORDER ONCALL 12 FEBRUARI 2026:

2 unit tronton 50 Cbm
Lokasi : cikokol
Waktu loading : segera
Rute/tujuan : CGK - SUB
driver  : AGENG
Nopol  : B 9654 YU
No hp  : +62 857-0738-0584
""")

add("""REQUEST ORDER ONCALL 12 FEBRUARI 2026:

3 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : Rosyit
Nopol  : B 9563 TEU
No hp  : 082313572678

Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : M.ibnu
Nopol  : L 9511 AL
No hp  : 082191633212

Waktu loading : 03:00
Rute/tujuan : CGK - SUB
driver  : Akiyat
Nopol  : L 9722 UE
No hp  :081281122738
""")

add("""REQUEST ORDER ONCALL 12 FEBRUARI 2026:

3 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : Rosyit
Nopol  : B 9563 TEU
No hp  : 082313572678

Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : M.ibnu
Nopol  : L 9511 AL
No hp  : 082191633212

Waktu loading : 03:00
Rute/tujuan : CGK - SUB
Revisi
driver  : Ahmad Wahyudi
Nopol  : W 8323 NV
No hp  : 085792725002
Posisi sudah dilokasi muat
""")

# Susulan 12 Feb
add("""REQUEST TAMBAHAN ORDER ULNG ONCALL  12 FEBRUARI 2026:

1 unit TRONTON 50 Cbm
Lokasi : cikokol
Waktu loading : 02:00  12/02/2026
Rute/tujuan : CGK - PKU
Nama \t: NASIP K
Nopol\t\t: BH 8165 QI
No Tlp\t\t:\u200a+6281272463920
""")

add("""REQUEST ULNG ORDER ONCALL 12 FEBRUARI 2026:
RAFAY
3 unit tronton 50 Cbm
Lokasi : cikokol
Waktu loading : segera
Rute/tujuan : CGK - MES
driver  : SRI MARDONO
Nopol  : BK 8678 VE
No hp  :085218843366
""")

add("""REQUEST ULANG ORDER ONCALL 12 FEBRUARI 2026:

2 unit tronton 50 Cbm
Lokasi : cikokol
Waktu loading : segera
Rute/tujuan : CGK - SUB
driver  : AGENG
Nopol  : B 9654 YU
No hp  : +62 857-0738-0584
""")

add("""REQUEST ULNG ORDER ONCALL 12 FEBRUARI 2026:

3 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : Rosyit
Nopol  : B 9563 TEU
No hp  : 082313572678

Waktu loading : SEGERA
driver  : M.ibnu
Nopol  : L 9511 AL
No hp  : 082191633212

Waktu loading : 03:00
driver  : Ahmad Wahyudi
Nopol  : W 8323 NV
No hp  : 085792725002
""")

# ============================================================
# 20 FEBRUARI 2026
# ============================================================
add("""Request Unit On Call Tgl 20 Feb 26

RAFAY

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/ 21-02-26
Rute/tujuan : CGK-JBR
Driver   : Arizal
Nopol  : B 9895 UXX
No Hp  :081229080317
""")

add("""Request Unit On Call Tgl 20 Feb 2026

1 unit twb 50 Cbm
Lokasi : Angke Poglar - Cikokol
Rute/ tuj : CGK - PKU
Waktu loading : 01:00 / 21-02-26
DRIVER 1 : ALPINASRI
DRIVER 2 :
NOPOL    : BM 8743 AU
NOHP      :081266347440
""")

add("""Request Unit On Call Tgl 20 Feb 2026

1 unit twb 50 Cbm
Lokasi : Angke Poglar - Cikokol
Rute/ tuj : CGK - MES
Waktu loading : 01:00 / 21-02-26
DRIVER 1 : suyoto
DRIVER 2 :
NOPOL    :  A8579 ZY
NOHP      : 081314527908
""")

add("""REQUEST ORDER ONCALL  20 FEBRUARI 2026:

2 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 23:00
Rute/tujuan : CGK - JATENG
driver  : AYUB
Nopol  : B 9976 KXW
No hp  :081220807285
""")

# Susulan 20 Feb JBR
add("""REQUEST ULANG ORDER ONCALL Tgl 20 Feb 26

RAFAY

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/ 21-02-26
Rute/tujuan : CGK-JBR
Driver   : Arizal
Nopol  : B 9895 UXX
No Hp  :081229080317
""")

# Susulan 20 Feb PKU+MES gabung
add("""REQUEST ULANG ORDER ONCALL Tgl 20 Feb 2026

1 unit twb 50 Cbm
Lokasi : Angke Poglar - Cikokol
Rute/ tuj : CGK - PKU
Waktu loading : 01:00 / 21-02-26
DRIVER 1 : ALPINASRI
DRIVER 2 :
NOPOL    : BM 8743 AU
NOHP      :081266347440

DRIVER 1 : suyoto
NOPOL    :  A8579 ZY
NOHP      : 081314527908
""")

# Susulan 20 Feb JATENG
add("""REQUEST ULANG ORDER ONCALL  20 FEBRUARI 2026:

2 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 23:00
Rute/tujuan : CGK - JATENG
driver  : AYUB
Nopol  : B 9976 KXW
No hp  :081220807285
""")

# ============================================================
# 21 FEBRUARI 2026
# ============================================================
add("""REQUEST ULANG DAN TAMBAHAN ORDER  ONCALL  21 FEBRUARI 2026

1 unit twb 50 CBM
Lokasi argo pantes 
Rute / tujuan : cgk - MES
Waktu loading : 03:00
Nama \t: RIO IRVAN
Nopol\t\t: BE 8019 HI
No Tlp\t:082281174064
""")

add("""Request Unit On Call Tgl 21 Feb 2026

1 unit twb 50 Cbm
Lokasi : Angke Poglar - Cikokol
Rute/ tuj : CGK - MES
Waktu loading : 01:00 / 22-02-26
DRIVER 1 : Aritonang 
DRIVER 2 :
NOPOL    : B 9756 UEU
NOHP      : +62 822-1709-8411
""")

add("""REQUEST ORDER ULANG ONCALL  21 FEBRUARI 2026:

2  unit TWB 50 Cbm
Lokasi : argopantes
Waktu loading : 23:00
Rute/tujuan : CGK -MES
driver  : Manulang
Nopol  : BK 8965 XJ
No hp  : +62 852-6229-9237

Driver : Ambar
Nopol : B 9023 UEX
No Hp : +62 813-9735-3306


2  unit TWB 50 Cbm
Lokasi : argopantes
Waktu loading : 20:00
Rute/tujuan : CGK -MES
driver  :
Nopol  :
No hp  :
""")

# Susulan 21 Feb MES (gabung RIO IRVAN + Aritonang)
add("""REQUEST ULANG DAN TAMBAHAN ORDER ONCALL  21 FEBRUARI 2026

1 unit twb 50 CBM
Lokasi argo pantes 
Rute / tujuan : cgk - MES
Waktu loading : 03:00
Nama \t: RIO IRVAN
Nopol\t\t: BE 8019 HI
No Tlp\t:082281174064

1 unit twb 50 Cbm
Lokasi : Angke Poglar - Cikokol
Rute/ tuj : CGK - MES
Waktu loading : 01:00 / 22-02-26
DRIVER 1 : Aritonang 
DRIVER 2 :
NOPOL    : B 9756 UEU
NOHP      : +62 822-1709-8411
""")

add("""REQUEST ORDER ULANG ONCALL  21 FEBRUARI 2026:

2  unit TWB 50 Cbm
Lokasi : argopantes
Waktu loading : 20:00
Rute/tujuan : CGK -MES
driver  : DIDIK DARMADI
Nopol  : BE 8235 UQ
No hp  :082306708981

Driver : DEDI MISWANTO
Nopol : BM 8012 ZU
No hp :083131828053
""")

# ============================================================
# 23-25 FEBRUARI 2026
# ============================================================
add("""REQUEST ORDER ONCALL 23 FEBRUARI 2026:


1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 12.00
Rute/tujuan : CGK - DPS
driver  : SANDJIWO
Nopol  : B 9147 SCJ
No hp  :0859106631400
""")

add("""REQUEST ORDER ONCALL 23 FEBRUARI 2026:


1 unit Cddl 24 Cbm
Lokasi : argo pantes
Waktu loading : Segera 
Rute/tujuan : CGK - Jatim tentatif

No Pol  :  F 9647 FH
Driver 1 :  TUMILAN
No HP :  0812-2910-3069
Driver 2 :  JATMIYANTA
No HP : 082118558105
""")

add("""Request Unit On Call Tgl 23 Feb 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/ 24-02-26
Rute/tujuan : CGK-JBR
Driver   : Agus
Nopol  :  B 9546 KXX
No Hp  : 081511075588
""")

# Susulan 23 Feb
add("""REQUEST ULANG ORDER ONCALL 23 FEBRUARI 2026:

1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 12.00
Rute/tujuan : CGK - DPS
driver  : SANDJIWO
Nopol  : B 9147 SCJ
No hp  :0859106631400
""")

add("""REQUEST ULANG ORDER ONCALL 23 FEBRUARI 2026:

1 unit Cddl 24 Cbm
Lokasi : argo pantes
Waktu loading : Segera 
Rute/tujuan : CGK - Jatim tentatif

No Pol  :  F 9647 FH
Driver 1 :  TUMILAN
No HP :  0812-2910-3069
Driver 2 :  JATMIYANTA
No HP : 082118558105
""")

add("""Request Unit On Call Tgl 24 Feb 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/ 25-02-26
Rute/tujuan : CGK-JBR
Driver   : Sandjiwo
Nopol  : B 9819 JXS
No Hp  :0859106631400
""")

add("""REQUEST ULNG ORDER ONCALL Tgl 23 Feb 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/ 24-02-26
Rute/tujuan : CGK-JBR
Driver   : Agus
Nopol  :  B 9546 KXX
No Hp  : 081511075588
""")

add("""Request Unit On Call Tgl 24 Feb 2026

1 unit twb 50 Cbm
Lokasi : Angke Poglar - Cikokol
Rute/ tuj : CGK - PKU
Waktu loading : 01:00 / 25-02-26
DRIVER 1 : ENDRA
DRIVER 2 :
NOPOL    : L 8791 UK
NOHP      :081210911369
""")

add("""REQUEST ORDER ONCALL  24 FEBRUARI 2026:

4 unit Cddl 24 Cbm
Lokasi : Argopantes
Waktu loading : SEGERA
Rute/tujuan : CGK - JATENG TENTATIF
driver  : TIRTA
Nopol  : B 9899 FRV
No hp  :085715144300
""")

# Susulan 24 Feb
add("""REQUEST ULANG ORDER ONCALL Tgl 24 Feb 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/ 25-02-26
Rute/tujuan : CGK-JBR
Driver   : Sandjiwo
Nopol  : B 9819 JXS
No Hp  :0859106631400
""")

add("""REQUEST ULANG ORDER ONCALL Tgl 24 Feb 2026

1 unit twb 50 Cbm
Lokasi : Angke Poglar - Cikokol
Rute/ tuj : CGK - PKU
Waktu loading : 01:00 / 25-02-26
DRIVER 1 : ENDRA
DRIVER 2 :
NOPOL    : L 8791 UK
NOHP      :081210911369
""")

add("""REQUEST ULANG ORDER ONCALL  24 FEBRUARI 2026:

4 unit Cddl 24 Cbm
Lokasi : Argopantes
Waktu loading : SEGERA
Rute/tujuan : CGK - JATENG TENTATIF
driver  : TIRTA
Nopol  : B 9899 FRV
No hp  :085715144300

Nama  : AYUB
Nopol : B 9976 KXW
No hp :081220807285
""")

add("""REQUEST ULANG ORDER ONCALL 25 FEBRUARI 2026:

1 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : segera
Rute/tujuan : CGK - MES
driver  : MANALU
Nopol  : B 9732 UEX
No hp  :+62 823-7004-2888
""")

add("""Request Unit On Call Tgl 25 Feb 26
RAFAY

1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 23:00
Rute/tujuan : CGK - DPS
driver  :Arizal
Nopol  :B 9895 UXX
No hp  :081229080317
""")

add("""REQUEST ORDER ONCALL 25 FEBRUARI 2026

2 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : WAHYUDI
Nopol  : N 9549 UA
No hp  :085784422398

Driver : SURYADI
Nopol : L 8183 UV
No hp :085729113217
""")

add("""Request Unit On Call Tgl 25 Feb 26

1 Unit  TWB 50 Cbm
Lokasi : Cikarang
Waktu loading : 06:00/ 26-02-26
Rute/tujuan : CKR-SUB-SUX 
Driver   : BAHRUL KHILMI
Nopol  : B 9608 EP
No Hp  :085731443815
""")

# Susulan 25 Feb
add("""REQUEST ULANG DAN TAMBAHAN ORDER ONCALL 25 FEBRUARI 2026:

1 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : segera
Rute/tujuan : CGK - MES
driver  : MANALU
Nopol  : B 9732 UEX
No hp  :+62 823-7004-2888
""")

add("""REQUEST ULANG ORDER ONCALL Tgl 25 Feb 26
RAFAY

1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 23:00
Rute/tujuan : CGK - DPS
driver  :Arizal
Nopol  :B 9895 UXX
No hp  :081229080317
""")

add("""REQUEST ULANG ORDER ONCALL 25 FEBRUARI 2026

2 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : WAHYUDI
Nopol  : N 9549 UA
No hp  :085784422398

Driver : SURYADI
Nopol : L 8183 UV
No hp :085729113217
""")

# ============================================================
# 26 FEBRUARI 2026
# ============================================================
add("""Request Unit On Call Tgl 26 Feb 2026

2 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : Segera
Rute/tujuan : CGK - JATENG
driver  :
Nopol  :
No hp  :

2 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : Segera
Rute/tujuan : CGK - JATIM
driver 1  : Jatmiyanta
No hp  : 082118558105
Driver 2 : Tumilan
No Hp : 0812-2910-3069
No pol  :  F 9647 FH

Data yg lain menyusul
""")

add("""REQUEST ORDER ULANG ONCALL

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : Rosyit
Nopol  : B 9562 TEU
No hp  :082313572678
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
26 FEBUARI 2026

2 UNIT TWB 50 CBM 
Lokasi : ARGOPANTES
Rute / tujuan : PKU
Waktu loading : SEGERA
Nama \t: SISWANTO
Nopol\t\t: B 9120 WXR
No Tlp\t:081943564062

Rute / tujuan : PKU
Waktu loading : 23:00
Nama \t: FERI IRAWAN
Nopol\t\t: BK 8516 W
No Tlp\t:085219216210
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
26 FEBUARI 2026

2 UNIT TWB 50 CBM 
Lokasi : ARGOPANTES
Rute / tujuan : PLM
Waktu loading : SEGERA
Nama \t: SANDRI
Nopol\t\t:  BE 9636 BU
No Tlp\t:+62 889-0702-0037
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
26 FEBUARI 2026

2 UNIT TWB 50 CBM
 Lokasi : ARGOPANTES
Rute / tujuan : MES
Waktu loading : SEGERA
Nama \t:Hendra setiawan
Nopol\t\t: BE 8023 WY
No Tlp\t:081280483919

Revisi
Rute / tujuan : MES
Waktu loading : 23:00
Nama \t: FEBRIANTO
Nopol\t\t: BA 9980 PS
No Tlp\t: 082286523993
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
26 FEBUARI 2026

Rute / tujuan : PLM
Waktu loading : 23:00
Nama \t: M Doni saputra
Nopol\t\t: BD 8423 B
No Tlp\t:082164544736
""")

add("""REQUER ORDER ULNG DAN TAMBAHAN ON CALL
26 FEBUARI 2026

2 UNIT TWB 50 CBM 
Lokasi : ARGOPANTES
Rute / tujuan : PKU
Waktu loading : SEGERA
Nama \t: Yusni gunawan
Nopol\t\t: BE 8951 BY
No Hp ; 085382785486

REVISI
Nama \t: MUJITO
Nopol\t\t: BE 8837 GK
No Hp ; 081269087474
""")

# Susulan 26 Feb - gabungan
add("""REQUEST ULANG ORDER ONCALL Tgl 26 Feb 2026

2 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : Segera
Rute/tujuan : CGK - JATENG
driver  :
Nopol  :
No hp  :

2 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : Segera
Rute/tujuan : CGK - JATIM
driver 1  : Jatmiyanta
No hp  : 082118558105
Driver 2 : Tumilan
No Hp : 0812-2910-3069
No pol  :  F 9647 FH

Data yg lain menyusul
""")

add("""REQUEST ULNG ORDER ONCALL

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : Rosyit
Nopol  : B 9562 TEU
No hp  :082313572678

driver  : AKIYAT
Nopol  : L 9722 UE
No hp  :081281122738
""")

add("""REQUEST ORDER ULANG ONCALL

2 UNIT TWB 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - MES
driver  : Aminullah
Nopol  : BD 8792 AO
No hp  : 083194225218

Data yg lain menyusul
""")

add("""Request Unit On Call Tgl 26 Feb 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/ 27-02-26
Rute/tujuan : CGK-JBR
Driver   : Davit
Nopol  : B 9726 SXW
No Hp  :082117275166
Revisi
""")

add("""REQUEST ULANG ORDER ONCALL

2 UNIT TWB 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - MES
driver  : Kudir
Nopol  : B 9380 UEX
No hp  : 0812-6218-9242

Data yg lain menyusul
""")

# ============================================================
# 27 FEBRUARI 2026
# ============================================================
add("""Request Order Oncall  27 Febuari 2026

2 UNIT TWB 50 CBM
Lokasi : JNE SURABAYA
Rute/ Tujuan   : SUX-CGK
Waktu loading : SEGERA
NAMA   : HABIB 
NOPOL : L 8336 UV
NO HP  :081231540625
""")

add("""Request Order Oncall  27 Febuari 2026

3 UNIT TWB 50 CBM
Lokasi : ARGOPANTES

Rute/ Tujuan   : SUB
Waktu loading : 15:00
NAMA   : ARIS
NOPOL : B 9139 SYT
NO HP  :081936963942
""")

add("""Request Order Oncall  27 Febuari 2026

2 UNIT TWB 50 CBM
Lokasi : JNE SURABAYA
Rute/ Tujuan   : SUX-CGK
Waktu loading : SEGERA
NAMA   : WAHYUDI
NOPOL : N 9549 UA
NO HP  : 085784422398
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
26 FEBUARI 2026
2 UNIT TWB 50 CBM
 Lokasi : ARGOPANTES

Revisi Nopol BA 9980 PS
Rute / tujuan : MES
Waktu loading : 23:00
Nama \t: SUPRIYANTO
Nopol\t\t: BE 8940 DB
No Tlp\t: 082389746001
""")

add("""ORDER ONCALL 27 FEBRUARI 2026:*


1 unit Cddl 24 Cbm
Lokasi : WangonGateway
Waktu loading : 12.00
Rute/tujuan : WGX-MGL-JOG
driver  : Agung prasetyo
Nopol  : B 9739 SEU
No hp  :085726344824
""")

add("""Request Unit On Call Tgl 27 Feb 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/ 28-02-26
Rute/tujuan : CGK-JBR
Driver   : Nana Hermawan
Nopol  : B 9658 TCP
No Hp  : 082261270165
Driver. : Rizki 
No hp. : 083180623289
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
26 FEBUARI 2026
2 UNIT TWB 50 CBM
 Lokasi : ARGOPANTES

Revisi Nopol BE 8831 CJ
Rute / tujuan : MES
Waktu loading : 23:00
Nama \t: DIAN SAPUTRA
Nopol\t\t: BE 8334 GBA
No Tlp\t: 08218218481
""")

add("""Request Order Oncall  27 Febuari 2026

2 UNIT TWB 50 CBM
Lokasi : JNE SURABAYA
Rute/ Tujuan   : SUX-CGK
Waktu loading : SEGERA
NAMA : AKIYAT
NOPOL : L 9722 UE
NO HP :081281122738

NAMA : ROSYIT
NOPOL : B 9562 TEU
NO HP :082313572678
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUES ULANG ORDER ON CALL DAN TAMBAHAN
27 FEBUARI 2026

2 UNIT TWB 50 CBM 
Lokasi : ARGOPANTES
Rute / tujuan : SUB
Waktu loading : 23:00
Nama \t: Yugik
Nopol\t\t: B 9810 UEU
No Tlp\t:085855134933

Rute / tujuan : SUB
Waktu loading : 23:00
Nama \t: Muatim
Nopol\t\t: H 9224 MA
No Tlp\t:08121615206
""")

# Susulan 27 Feb
add("""ORDER ULANG ONCALL 27 FEBRUARI 2026:*

1 unit Cddl 24 Cbm
Lokasi : WangonGateway
Waktu loading : 12.00
Rute/tujuan : WGX-MGL-JOG
driver  : Agung prasetyo
Nopol  : B 9739 SEU
No hp  :085726344824
""")

add("""REQUEST ULNG Order Oncall  27 Febuari 2026

2 UNIT TWB 50 CBM
Lokasi : JNE SURABAYA
Rute/ Tujuan   : SUX-CGK
Waktu loading : SEGERA
NAMA   : HABIB 
NOPOL : L 8336 UV
NO HP  :081231540625

NAMA   : WAHYUDI
NOPOL : N 9549 UA
NO HP  : 085784422398

NAMA : AKIYAT
NOPOL : L 9722 UE
NO HP :081281122738

NAMA : ROSYIT
NOPOL : B 9562 TEU
NO HP :082313572678
""")

add("""[05:31, 07/03/2026] Akbar Rafay: Request Order Oncall  27 Febuari 2026

3 UNIT TWB 50 CBM
Lokasi : ARGOPANTES

Rute/ Tujuan   : SUB
Waktu loading : 15:00
NAMA   : Jamaadi
NOPOL : L 8786 BN
NO HP  :082229973792

NAMA : Ibnu
NOPOL : L 9511 AL
NO HP :082191633212
""")

add("""REQUEST ULANG Order Oncall  27 Febuari 2026

3 UNIT TWB 50 CBM
Lokasi : ARGOPANTES

Rute/ Tujuan   : SUB
Waktu loading : 15:00
NAMA   : Jamaadi
NOPOL : L 8786 BN
NO HP  :082229973792

NAMA   : ARIS
NOPOL : B 9139 SYT
NO HP  :081936963942

NAMA : Ibnu
NOPOL : L 9511 AL
NO HP :082191633212
""")

add("""REQUES ULANG ORDER ON CALL DAN TAMBAHAN
27 FEBUARI 2026

2 UNIT TWB 50 CBM 
Lokasi : ARGOPANTES
Rute / tujuan : SUB
Waktu loading : 23:00
Nama \t: Yugik
Nopol\t\t: B 9810 UEU
No Tlp\t:085855134933

Rute / tujuan : SUB
Waktu loading : 23:00
Nama \t: Muatim
Nopol\t\t: H 9224 MA
No Tlp\t:08121615206
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUER ORDER ULANG DAN TAMBAHAN ON CALL
26 FEBUARI 2026

2 UNIT TWB 50 CBM 
Lokasi : ARGOPANTES
Rute / tujuan : PKU
Waktu loading : SEGERA
Nama \t: Yusni gunawan
Nopol\t\t: BE 8951 BY
No Hp ; 085382785486
""")

# ============================================================
# 28 FEBRUARI 2026
# ============================================================
add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ULANG ORDER ONCALL 28 FEBRUARI 2026:

3 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 11:00
Rute/tujuan : CGK - JATIM
driver  : Agus Supriatna 
Nopol  :B 9546 KXX
No hp  :081511075588

Data yg lain menyusul
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ULANG ORDER ONCALL 28 FEBRUARI 2026:

1 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 11:00
Rute/tujuan : CGK - JATIM
driver  : Rizky / Aris
Nopol  : B9091SCJ
No hp  : 081646057656 / 085601390708
""")

# Susulan 28 Feb JATIM gabung
add("""REQUEST ULNG ORDER ONCALL 28 FEBRUARI 2026:

3 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 11:00
Rute/tujuan : CGK - JATIM
driver  : Agus Supriatna 
Nopol  :B 9546 KXX
No hp  :081511075588

driver  : Rizky / Aris
Nopol  : B9091SCJ
No hp  : 081646057656 / 085601390708

Data yg lain menyusul
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUER ORDER ULANG DAN TAMBAHAN ON CALL
28 FEBUARI 2026

5 UNIT CDDL 24 CBM 
Lokasi : ARGOPANTES
Rute / tujuan : JATENG TENTATIF
Waktu loading : SEGERA
Nama : Dedeng
Nopol :E 9426 Aa
No.hp : 0895393659401
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ONCALL 28 FEBRUARI 2026:


2 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 23:00
Rute/tujuan : CGK - JATENG
Nama: indra
Nopol:B9588YM
No hp:082295768103
""")

# Susulan 28 Feb JATENG gabung
add("""REQUER ULNG DAN TAMBAHAN ORDER ONCALL 28 FEBUARI 2026

5 UNIT CDDL 24 CBM 
Lokasi : ARGOPANTES
Rute / tujuan : JATENG TENTATIF
Waktu loading : SEGERA
Nama : Dedeng
Nopol :E 9426 Aa
No.hp : 0895393659401

Nama : indra
Nopol:B9588YM
No hp:082295768103
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ULANG ONCALL 28/02/206

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 00:00
Rute/tujuan : CGK - PKU
driver  : ARIANSYAH
Nopol  : BE 8775 DY
No hp  :083142572937
""")

# Susulan 28 Feb PKU
add("""REQUEST ULNG ORDER ONCALL 28/02/2026

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 00:00
Rute/tujuan : CGK - PKU
driver  : ARIANSYAH
Nopol  : BE 8775 DY
No hp  :083142572937

driver  : SISWANTO
Nopol  : B 9120 WXR
No hp  : 081943564062
""")

# ============================================================
# 1 MARET 2026
# ============================================================
add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ONCALL 1 Maret 2026:

3 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading :  28/02/2026
Rute/tujuan : CGK - MES
driver : ARBI
Nopol : BE 8919 AMN
No hp :082237978236

Waktu loading : 12:00
Rute/tujuan : CGK - MES
driver  : ANTON
Nopol  : BE 9063 AR
No hp  :083181833620
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ONCALL 1 Maret 2026:

3 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : 04;00 28/02/2026
Rute/tujuan : CGK - MES
driver  : Jodi akbar 
Nopol  : BE 8013 AU
No hp  :085693461006
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ONCALL 1 Maret 2026:

3 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : Segera 28/02/2026
Waktu loading : 21:00
Rute/tujuan : CGK - MES

driver  : FIRMAN
Nopol  : BB 8373 LG
No hp  :+62 838-9253-2819
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ONCALL 1 Maret 2026:

3 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading :  28/02/2026
Rute/tujuan : CGK - MES
driver : ARBI
Nopol : BE 8919 AMN
No hp :082237978236

Waktu loading : 00:00
Rute/tujuan : CGK - MES
driver  : ANTON
Nopol  : BE 9063 AR
No hp  :083181833620
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUEST ORDER ONCALL 1 Maret 2026:


2 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : SEGERA
Rute/tujuan : CGK - JATENG
driver  : Alex S
Nopol  : B 9411 VXR
No hp  : 088212698834
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REVISI Nopol BE 9063 AR

REQUEST ORDER ONCALL 1 Maret 2026:
3 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : 00:00
Rute/tujuan : CGK - MES
driver  : madi
Nopol  : BA 9750 
No hp  : +62 852-7850-3227
""")

# Susulan 1 Maret - gabungan semua driver MES
add("""REQUEST ULANG ORDER ONCALL 1 Maret 2026:

3 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading :  28/02/2026
Rute/tujuan : CGK - MES
driver : ARBI
Nopol : BE 8919 AMN
No hp :082237978236

Waktu loading : 12:00
driver  : ANTON
Nopol  : BE 9063 AR
No hp  :083181833620

driver  : Jodi akbar 
Nopol  : BE 8013 AU
No hp  :085693461006

driver  : FIRMAN
Nopol  : BB 8373 LG
No hp  :+62 838-9253-2819
""")

add("""REQUEST ULANG ORDER ONCALL 1 Maret 2026:

3 UNIT TWB 50 Cbm
Lokasi : ARGOPANTES
Waktu loading : 00:00
Rute/tujuan : CGK - MES
driver  : madi
Nopol  : BA 9750 
No hp  : +62 852-7850-3227
""")

add("""REQUEST ULANG ORDER ONCALL 1 Maret 2026:

2 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : SEGERA
Rute/tujuan : CGK - JATENG
driver  : Alex S
Nopol  : B 9411 VXR
No hp  : 088212698834
""")

add("""[05:31, 07/03/2026] Akbar Rafay: REQUER ORDER ULANG DAN TAMBAHAN ON CALL
26 FEBUARI 2026

2 UNIT TWB 50 CBM 
Lokasi : ARGOPANTES
Rute / tujuan : PKU
Waktu loading : SEGERA
REVISI
Nama \t: MUJITO
Nopol\t\t: BE 8837 GK
No Hp ; 081269087474
""")

# ============================================================
# 3 MARET 2026
# ============================================================
add("""REQUEST  ORDER  ONCALL  3 MARET 2026

5 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : Segera
Rute/tujuan : CGK - PKU
driver  : Soni Rahmat
Nopol  : BM 8142 RY
No hp  : 082282001964

Waktu loading : 15;00
Rute/tujuan : CGK - PKU
driver  :
Nopol  :
No hp  :

Waktu loading : 20:00
Rute/tujuan : CGK - PKU
driver  :
Nopol  :
No hp  :

Waktu loading : 02:00/04-03-2026
Rute/tujuan : CGK - PKU 
driver  :
Nopol  :
No hp  :

Waktu loading : 07:00/04-03-2026
Rute/tujuan : CGK - PKU 
driver  :
Nopol  :
No hp  :
""")

add("""Request Unit On Call Tgl 03 Mar 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikarang
Waktu loading : 06:00/  04 Mar 26
Rute/tujuan : CKR-JBR
Driver   : Nana hermawan
Nopol  : B 9658 TCP
No Hp  :082261270165
""")

add("""Request Unit On Call *Tgl 03 Mar 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikarang
Waktu loading : 06:00/  04 Mar 26
Rute/tujuan : CKR-MXG
Driver   : Davit
Nopol  : B 9726 SXW
No Hp  :082117275166
""")

add("""REQUEST  ORDER  ONCALL  3 MARET 2026

5 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 23:00
Rute/tujuan : CGK - MES 
ddriver  : Sri Mardono
Nopol  : BK 8678 VE
No hp  : 085218843366

Waktu loading : 03:00/04-03-2026
Rute/tujuan : CGK - MES 
driver  :
Nopol  :
No hp  :
""")

add("""REQUEST  ORDER  ONCALL  3 MARET 2026

6 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 23:00
Rute/tujuan : CGK - SUB 
driver  : Rosyit
Nopol  : B 9562 TEU
No hp  : 082313572678

Driver : sofyan
Nopol : B 9679WT
No Hp : 082231837381
""")

add("""REQUEST  ORDER  ONCALL  3 MARET 2026

1 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 23:00
Rute/tujuan : SUB - CGK
driver  : Yuda
Nopol  : W 8973 UQ
No hp  : 089507296985
""")

add("""REQUEST ORDER ONCALL 03 maret 2026:

3 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 23:00
Rute/tujuan : CGK - JATIM
driver  : Ari purnama
Nopol  : B 9383 TXV
No hp : 082136689169


Fyi pak  @Unknown user@Unknown user
""")

# Susulan 3 Maret
add("""REQUEST ULANG ORDER ONCALL 3 MARET 2026

5 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : Segera
Rute/tujuan : CGK - PKU
driver  : Soni Rahmat
Nopol  : BM 8142 RY
No hp  : 082282001964

Waktu loading : 15;00
driver  :
Nopol  :
No hp  :

Waktu loading : 20:00
driver  :
Nopol  :
No hp  :

Waktu loading : 02:00/04-03-2026
driver  :
Nopol  :
No hp  :

Waktu loading : 07:00/04-03-2026
driver  : Jupri
Nopol  : BM 9273 RO
No hp  : 082172471454
""")

add("""REQUEST ULANG ORDER ONCALL 3 MARET 2026

5 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 23:00
Rute/tujuan : CGK - MES 
ddriver  : Sri Mardono
Nopol  : BK 8678 VE
No hp  : 085218843366

Waktu loading : 03:00/04-03-2026
driver  : Andi
Nopol  : BE 8456 FN
No hp  : +62 853-7337-2594
""")

add("""REQUEST ULANG ORDER ONCALL 3 MARET 2026

6 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 23:00
Rute/tujuan : CGK - SUB 
driver  : Rosyit
Nopol  : B 9562 TEU
No hp  : 082313572678

Driver : sofyan
Nopol : B 9679WT
No Hp : 082231837381

driver  : SAMOSIR
Nopol  : B 9727 UEX
No hp  :+62 822-7429-6236
""")

add("""REQUEST ULANG ORDER ONCALL 3 MARET 2026

1 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 23:00
Rute/tujuan : SUB - CGK
driver  : Yuda
Nopol  : W 8973 UQ
No hp  : 089507296985
""")

add("""REQUEST ULANG ORDER ONCALL 03 maret 2026:

3 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : 23:00
Rute/tujuan : CGK - JATIM
driver  : Ari purnama
Nopol  : B 9383 TXV
No hp : 082136689169


Fyi pak  @Unknown user@Unknown user
""")

# ============================================================
# 4-6 MARET 2026
# ============================================================
add("""REQUEST ULANG ORDER ONCALL 04 MARET 2026:

8 unit Cddl 24 Cbm
Lokasi : *argo pantes *
Waktu loading : segera
Rute/tujuan : *CGK - Jateng tentatif
Nama : Dedeng
Nopol :E 9426 Aa
No.hp : 0895393659401
""")

add("""Request Unit On Call Tgl 04 Maret 2026
5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA
Rute/tujuan : CGK - PKU

driver  : Jupri
Nopol  : BM 9273 RO
No Hp :082172471454
""")

add("""REQUEST ORDER ONCALL
04 MARET 2026:

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA 
Rute/tujuan : CGK - MES
driver  : Andi
Nopol  : BE 8610 DB
No Hp :081374328877

Waktu loading : SEGERA 
Rute/tujuan : CGK - MES
driver  : Misno
Nopol  : BN 8038 RP
No Hp :082211762649
""")

add("""REQUEST ORDER ONCALL
04 MARET 2026:

REVISI NOPOL BE 8610 DB

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA 
Rute/tujuan : CGK - MES
driver  : Usman Afandi
Nopol  : BE 8456 FN
No Hp : +62 853-7337-2594
""")

add("""Request Order Oncall  04 Mar 2026

2 UNIT TWB 50 CBM
Lokasi : JNE SURABAYA
Rute/ Tujuan   : SUX-CGK
Waktu loading : SEGERA
NAMA   : Wahyudi
NOPOL : N 9549 UA
NO HP : 085784422398
""")

# Susulan 04 Maret
add("""REQUEST ULANG ORDER ONCALL 04 MARET 2026:

8 unit Cddl 24 Cbm
Lokasi : *argo pantes *
Waktu loading : segera
Rute/tujuan : *CGK - Jateng tentatif
Nama : Dedeng
Nopol :E 9426 Aa
No.hp : 0895393659401

Nama  : Jupri
Nopol : BM 9273 RO
No Hp :082172471454
""")

add("""REQUEST ULANG ORDER ONCALL
04 MARET 2026:

REVISI NOPOL BE 8610 DB

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : SEGERA 
Rute/tujuan : CGK - MES
driver  : Andi
Nopol  : BE 8610 DB
No Hp :081374328877

driver  : Usman Afandi
Nopol  : BE 8456 FN
No Hp : +62 853-7337-2594

driver  : Misno
Nopol  : BN 8038 RP
No Hp :082211762649
""")

add("""REQUEST ULANG Order Oncall  04 Mar 2026

2 UNIT TWB 50 CBM
Lokasi : JNE SURABAYA
Rute/ Tujuan   : SUX-CGK
Waktu loading : SEGERA
NAMA   : Wahyudi
NOPOL : N 9549 UA
NO HP : 085784422398

NAMA : AKIYAT
NOPOL : L 9722 UE
NO HP :081281122738
""")

add("""Request Unit On Call Tgl 05 Mar 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikarang
Waktu loading : 06:00/  06 Mar 26
Rute/tujuan : CKR-JBR
Driver   : miyanta
Nopol  : F 9647 FH
No Hp  :08118558105
""")

add("""Request Unit On Call Tgl 05 Mar 26
RAFAY

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/  06  Mar 26
Rute/tujuan : CGK-PSR
Driver   : Davit
Nopol  : B 9726 SXW
No Hp  :082117275166
""")

add("""REQUEST ORDER ONCALL
05 MARET 2026:

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : 17:00/05-03-2026 
Rute/tujuan : CGK - SUB
driver  : Iwan Hariono
Nopol  : BL 8188 JP
No Hp :081389976421
""")

add("""Request Order Oncall  05 Maret  2026

2 UNIT TWB 50 CBM
Lokasi : JNE SURABAYA
Rute/ Tujuan   : SUX-CGK
Waktu loading : SEGERA
Driver : Akiyat
Nopol : L 9722 UE
No HP :081281122738
""")

# Susulan 05 Maret
add("""REQUEST ULANG Order Unit On Call Tgl 05 Mar 26

1 Unit  Cddl / 24 Cbm
Lokasi : Cikarang
Waktu loading : 06:00/  06 Mar 26
Rute/tujuan : CKR-JBR
Driver   : miyanta
Nopol  : F 9647 FH
No Hp  :08118558105
""")

add("""REQUEST ULANG Order Unit On Call Tgl 05 Mar 26
RAFAY

1 Unit  Cddl / 24 Cbm
Lokasi : Cikokol + Cikarang
Waktu loading : 03:00/  06  Mar 26
Rute/tujuan : CGK-PSR
Driver   : Davit
Nopol  : B 9726 SXW
No Hp  :082117275166
""")

add("""REQUEST ULANG ORDER ONCALL 05 MARET 2026:

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : 17:00/05-03-2026 
Rute/tujuan : CGK - SUB
driver  : Iwan Hariono
Nopol  : BL 8188 JP
No Hp :081389976421

Waktu loading : SEGERA
driver  : Yuda
Nopol  : W 8973 UQ
No hp  : 089507296985
""")

add("""REQUEST ULANG Order Oncall  05 Maret  2026

2 UNIT TWB 50 CBM
Lokasi : JNE SURABAYA
Rute/ Tujuan   : SUX-CGK
Waktu loading : SEGERA
Driver : Akiyat
Nopol : L 9722 UE
No HP :081281122738

Driver : Wahyudi
Nopol : N 9549 UA
No HP :085784422398
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
06 MARET 2026

3 UNIT TWB 50 CBM
 Lokasi : ARGOPANTES
Rute / tujuan : *JATim TENTATIF
Waktu loading : SEGERA
Nama \t: M. Ibnu
Nopol\t\t: L 9511 AL
No Tlp\t:082191633212

Nama : Jamaadi
Nopol : L 8786 BN
No Hp :082229973792

Nama : Suryadi 
Nopol : L 8183UV
No hp :085729113217
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
06 MARET 2026

3 UNIT TWB 50 CBM
 Lokasi : ARGOPANTES
Rute / tujuan : CGK-SUB
Waktu loading : SEGERA
Nama \t: Yuda
Nopol\t\t: W 8973 UQ
No Tlp\t:089507296985
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
06 MARET 2026
DATA SUMATERA

2 UNIT TWB 50 CBM
 Lokasi : ARGOPANTES
Rute / tujuan : PKU
Waktu loading : SEGERA
Nama \t: Ridwan
Nopol\t\t: BK 8330 VY
No Tlp\t: 082382200400


Fyi pak @\u2060Sobar JNE\u2069 data tambahan nya
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
06 MARET 2026
DATA SUMATERA
2 UNIT TWB 50 CBM
 Lokasi : ARGOPANTES
Rute / tujuan : PKU
Waktu loading : SEGERA

Nama \t: Nasip
Nopol\t\t: BH 8165 QI
No Tlp\t:+6281272463920
""")

add("""REQUER ORDER ULANG DAN TAMBAHAN ON CALL
06 MARET 2026

3 UNIT TWB 50 CBM
 Lokasi : ARGOPANTES
Rute / tujuan : CGK-SUB
Waktu loading : SEGERA
Nama \t: Wahyudi
Nopol\t\t: N 9549 UA
No Tlp\t:085784422398

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES
Waktu loading : 18:00/05-02-2026 
Rute/tujuan : CGK - PKU
driver  : Syarial
Nopol  :BM 8486 AU
No Hp :081317708658
""")

# Tulis output ke file
output_text = "\n".join(output_lines)
with open(r"dataset feb-mar\dataset_feb_mar_paired.txt", "w", encoding="utf-8") as f:
    f.write(output_text)

print(f"File berhasil dibuat dengan {len(output_lines)} blok pesanan.")
print(f"Total karakter: {len(output_text)}")
