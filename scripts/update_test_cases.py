
import json
import os

CASES_FILE = "tests/fixtures/expanded_cases.json"

REFERENCE_ANSWERS = {
    1: "Tak boleh la bro, aku tak ada duit sekarang. Nanti la kita jumpa.",
    2: "Macam mana nak buat ni? Aku dah cuba banyak kali tapi tak jadi.",
    3: "Benda ni memang best gila!",
    4: "Jom lepak mamak, aku belanja teh tarik.",
    5: "Eh bro, macam mana meeting tadi? Client puas hati tak?",
    6: "Geram betul dengan servis ni, lambat macam siput.",
    7: "Jangan kacau aku, mengantuk sangat lepas sahur.",
    8: "Demo tak makan nasi kerabu lagi ke?",
    9: "Kenapa mu tak datang semalam?",
    10: "Hang nak pergi mana tu? Nampak segak semacam.",
    11: "Kenapa hang tak bagitahu awal-awal?",
    12: "Kena la makan masak lemak cili api, baru sedap.",
    13: "Kau jangan bising, aku nak tidur ni.",
    14: "Kitak orang dah makan belum?",
    15: "Kamek nak pergi pasar kejap.",
    16: "Boleh bah, kalau kau mahu.",
    17: "Tak payah la kau susah-susah.",
    18: "Anda boleh memperbaharui lesen memandu di JPJ, UTC, Pejabat Pos, atau melalui MyEG.",
    19: "Subjek: Permohonan Cuti Sakit\n\nKepada HR,\n\nSaya ingin memohon cuti sakit untuk esok kerana tidak sihat. Sijil sakit akan disertakan.",
    20: "Resepi nasi lemak simple: Masak nasi dengan santan, halia, dan daun pandan. Hidangkan dengan sambal ikan bilis, telur rebus, timun, dan kacang.",
    21: "Apa khabar bro? Ada cerita apa?",
    22: "Bosan betul mat, kerja banyak gila.",
    23: "Stress betul mental aku hari ini.",
    24: "Dia tu berlagak je lebih.",
    25: "Jangan buat hal lah wei.",
    26: "Persembahan dia tadi memang padu teruk.",
    27: "Aku setuju je kalau korang setuju.",
    28: "Tak ada masalah lah, tu benda kecil je.",
    29: "Untuk install Python di Mac, buka Terminal dan taip 'brew install python'. Pastikan Homebrew dah install.",
    30: "The best time to visit Langkawi is during the dry season, from November to April.",
    31: "Rukun Negara ialah ideologi kebangsaan Malaysia yang mempunyai 5 prinsip: Kepercayaan kepada Tuhan, Kesetiaan kepada Raja dan Negara, Keluhuran Perlembagaan, Kedaulatan Undang-undang, Kesopanan dan Kesusilaan.",
    32: "Perdana Menteri Malaysia sekarang ialah Datuk Seri Anwar Ibrahim.",
    33: "Tarikh Hari Raya Aidilfitri berubah setiap tahun mengikut kalendar Islam (Syawal). Sila semak tarikh rasmi.",
    34: "Tempat dating best kat KL: KLCC Park, Pavilion, Aquaria KLCC, atau cafe di Bukit Bintang.",
    35: "Jalan sesak teruk di Federal Highway sekarang. Guna Waze untuk cari jalan alternatif.",
    36: "Musang King murah boleh cari di kawasan SS2 Petaling Jaya atau terus ke Raub, Pahang.",
    37: "Sila semak ramalan cuaca terkini di laman web MetMalaysia atau aplikasi cuaca.",
    38: "Dalam bahasa Kelantan, 'I love you' boleh disebut 'Kawe sayang demo'.",
    39: "Gostan bermaksud 'undur' atau 'reverse', selalunya digunakan untuk kenderaan.",
    40: "Dalam bahasa Sarawak, 'atuh' atau 'aduh' ialah ungkapan sakit.",
    41: "Canoneer ialah minion yang membawa meriam dalam permainan Mobile Legends atau League of Legends.",
    42: "Untuk kira 50 USD ke MYR, darabkan dengan kadar tukaran semasa (contohnya 4.5). Jadi sekitar RM225.",
    43: "Buah cempedak di luar pagar,\nAmbil galah tolong jolokkan;\nSaya budak baru belajar,\nKalau salah tolong tunjukkan. (Contoh pantun cinta: Dua tiga kucing berlari, Mana nak sama si kucing belang...)",
    44: "Saya ingin memaklumkan perletakan jawatan saya berkuatkuasa serta-merta (notis 24 jam). Terima kasih atas peluang yang diberikan.",
    45: "Kalau nak pedas, saya cadangkan makan Nasi Lemak Sambal Sotong, Tomyam, atau Laksa.",
    46: "Sila cari klinik 24 jam terdekat menggunakan Google Maps atau Waze.",
    47: "Kalau kereta rosak tepi jalan, call nombor bantuan insurans anda untuk towing percuma, atau PLUS ronda jika di lebuhraya.",
    48: "Untuk claim insurans kemalangan: Buat report polis dalam 24 jam, ambil gambar kerosakan, dan hubungi ejen insurans anda.",
    49: "Resepi Ayam Masak Merah: Goreng ayam kunyit separuh masak. Tumis bawang, cili kisar, sos cili, sos tomato. Masukkan ayam dan gaul rata.",
    50: "Sabar, memang bahaya kalau driver tak bagi signal. Hati-hati memandu.",
    51: "Grammar yang betul ialah: 'I went to school yesterday' (sebab past tense 'yesterday').",
    52: "SPM ialah peperiksaan Tingkatan 5. STPM ialah Tingkatan 6 (Pra-Universiti) yang setaraf dengan A-Level/Matrikulasi.",
    53: "UiTM stands for Universiti Teknologi MARA.",
    54: "Syarat kemasukan Matrikulasi: Warganegara Malaysia, lulus SPM dengan kredit dalam BM, BI, Matematik, dan subjek sains berkaitan.",
    55: "Taman Negara yang popular di Malaysia: Taman Negara Pahang, Taman Negara Bako (Sarawak), Taman Kinabalu (Sabah).",
    56: "PDPR ialah Pengajaran dan Pembelajaran di Rumah (Home-based Learning).",
    57: "Lagu 'Lemak Manis' dinyanyikan oleh Roslan Madun.",
    58: "Undi 18 bermaksud warganegara berumur 18 tahun ke atas layak mengundi secara automatik.",
    59: "Untuk mendaftar PADU (Pangkalan Data Utama), layari laman web rasmi PADU dan isi maklumat profil anda.",
    60: "Harga minyak RON95 terkini masih disubsidi pada RM2.05 seliter (sehingga pengumuman subsidi bersasar).",
    61: "Touch 'n Go eWallet selamat digunakan kerana dikawal selia oleh Bank Negara Malaysia. Jangan kongsi OTP.",
    62: "Kalau scammer call cakap LHDN, letak telefon terus. Jangan layan. LHDN tak akan call guna nombor handphone peribadi.",
    63: "Saman PDRM boleh dibayar online melalui MyBayar Saman atau mesin ATM.",
    64: "Kaunter JPJ biasanya buka 8 pagi hingga 5 petang (Isnin-Jumaat). UTC buka sampai malam dan hujung minggu.",
    65: "Renew passport boleh walk-in untuk warga emas, OKU, dan kanak-kanak. Orang dewasa digalakkan buat online appointment.",
    66: "Cuti umum Malaysia 2024 termasuk Hari Raya, Tahun Baru Cina, Deepavali, Krismas, Hari Kebangsaan, dan Hari Malaysia.",
    67: "Baju Melayu Cekak Musang ada butang dan kolar tinggi. Teluk Belanga tiada kolar (leher bulat) dan satu butang.",
    68: "Dalam adat Melayu, merisik tidak wajib tetapi digalakkan untuk kenal latar belakang keluarga.",
    69: "Hantaran tunang biasanya nombor ganjil, contohnya 5 dulang berbalas 7.",
    70: "Pantang larang orang mengandung dulu-dulu: Jangan paku dinding, jangan duduk di pintu, jangan keluar waktu senja.",
    71: "Lagu raya legend: 'Suasana Hari Raya' (Anuar & Ellina), 'Balik Kampung' (Sudirman), 'Dendang Perantau' (P. Ramlee).",
    72: "Filem P. Ramlee paling lawak: 'Madu Tiga', 'Seniman Bujang Lapok', 'Pendekar Bujang Lapok'.",
    73: "Pemenang AJL (Anugerah Juara Lagu) tahun lepas ialah Aina Abdul (Terus Hidup) - *contoh*.",
    74: "Panggung wayang terdekat boleh dicari guna Google Maps (GSC/TGV).",
    75: "Harga tiket konsert Coldplay di Malaysia bermula dari RM228 hingga RM3000+.",
    76: "Keputusan bola sepak Malaysia vs Korea: Malaysia seri 3-3 (Piala Asia 2023).",
    77: "Dato' Lee Chong Wei bersara pada tahun 2019.",
    78: "Badminton court near me: Search Google Maps untuk gelanggang badminton terdekat.",
    79: "JDT (Johor Darul Ta'zim) sering menang Liga Super Malaysia.",
    80: "Sukan SEA seterusnya akan diadakan di Thailand (2025) dan Malaysia (2027).",
    81: "Hiking trail best di Selangor: Bukit Broga, Bukit Gasing, Bukit Saga, Air Terjun Chiling.",
    82: "Tempat camping tepi sungai: Janda Baik, Hulu Langat, Gopeng.",
    83: "Harga gym membership Fitness First sekitar RM150-RM250 sebulan bergantung pakej.",
    84: "Menu Diet Atkins Malaysia: Telur rebus, ayam goreng kunyit (tanpa nasi), sup sayur, ikan bakar.",
    85: "Untuk report jalan berlubang, guna aplikasi MyJalan KKR.",
    86: "Kalau jiran bising malam-malam, boleh report polis atas gangguan ketenteraman awam (nuisance).",
    87: "Aduan sampah tak kutip boleh dibuat kepada PBT (Majlis Perbandaran) atau KDEB Waste Management (Selangor).",
    88: "Aduan anjing liar boleh dibuat kepada Jabatan Kesihatan/Vektor PBT kawasan anda.",
    89: "Talian hotline Air Selangor (Syabas) ialah 15300.",
    90: "Kalau blackout rumah sorang je, check DB box (tendang fius). Kalau satu taman, call TNB Careline 15454.",
    91: "Kalau internet Unifi slow, restart router dulu. Kalau tak okey, report guna aplikasi myUnifi.",
    92: "Masalah line Celcom tiada signal, cuba on/off flight mode atau report ke Celcom.",
    93: "MyTV tak dapat siaran: Check antenna, scan semula channel, atau pastikan decoder on.",
    94: "Kalau Grab driver cancel last minute, boleh report dalam app Grab di bahagian 'Help Centre'.",
    95: "Shopee delivery lambat: Check tracking number. Kalau peram lama sangat, contact customer service Shopee.",
    96: "Foodpanda wrong order: Tangkap gambar makanan, report dalam app Foodpanda untuk refund.",
    97: "Kesimpulan essay kemerdekaan: Kemerdekaan bukan sekadar bebas penjajah, tapi membina jati diri bangsa.",
    98: "Beza 'affect' dan 'effect': Affect ialah kata kerja (kesan kepda), Effect ialah kata nama (akibat/hasil).",
    99: "Resume yang baik perlu ringkas (1-2 muka surat), ada maklumat kontak, pengalaman kerja, dan kemahiran relevan.",
    100: "Tips interview kerja: Datang awal, berpakaian kemas, buat research pasal company, dan jawab dengan yakin.",
}

def update_cases():
    if not os.path.exists(CASES_FILE):
        print(f"File not found: {CASES_FILE}")
        return

    with open(CASES_FILE, 'r') as f:
        cases = json.load(f)

    updated_count = 0
    for case in cases:
        cid = case.get("id")
        if cid in REFERENCE_ANSWERS:
            case["reference_answer"] = REFERENCE_ANSWERS[cid]
            updated_count += 1

    with open(CASES_FILE, 'w') as f:
        json.dump(cases, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully updated {updated_count} cases with reference answers.")

if __name__ == "__main__":
    update_cases()
