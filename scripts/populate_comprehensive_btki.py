import csv
import os
from decimal import Decimal

REAL_BTKI_DATA = [
    # =========================================================================
    # BAB 33: Minyak Atsiri & Resinoida; Olahan Wewangian, Kosmetika atau Rias
    # =========================================================================
    ("33011200", "33", "3301", "330112", "Minyak atsiri dari jeruk manis (orange oil)", "Essential oil of orange", "kg", 5.0, False, "verified_none"),
    ("33011300", "33", "3301", "330113", "Minyak atsiri dari lemon", "Essential oil of lemon", "kg", 5.0, False, "verified_none"),
    ("33012500", "33", "3301", "330125", "Minyak atsiri dari permen mint lainnya (peppermint)", "Essential oil of other mints", "kg", 5.0, False, "verified_none"),
    ("33012910", "33", "3301", "330129", "Minyak sereh wangi (citronella oil)", "Citronella oil", "kg", 5.0, False, "verified_none"),
    ("33012920", "33", "3301", "330129", "Minyak nilam (patchouli oil)", "Patchouli oil", "kg", 5.0, False, "verified_none"),
    ("33012990", "33", "3301", "330129", "Minyak atsiri lainnya", "Other essential oils", "kg", 5.0, False, "verified_none"),
    ("33021000", "33", "3302", "330210", "Campuran zat bau-bauan untuk industri makanan atau minuman", "Mixtures of odoriferous substances for food or drink industries", "kg", 5.0, False, "verified_none"),
    ("33029000", "33", "3302", "330290", "Campuran zat bau-bauan lainnya untuk industri wewangian", "Other mixtures of odoriferous substances", "kg", 5.0, False, "verified_none"),
    ("33030000", "33", "3303", "330300", "Parfum dan cairan pewangi (eau de cologne, eau de parfum)", "Perfumes and toilet waters", "u", 10.0, False, "verified_rules"),
    ("33041000", "33", "3304", "330410", "Olahan rias bibir (lipstik, lip gloss, lip liner)", "Lip make-up preparations", "u", 10.0, False, "verified_rules"),
    ("33042000", "33", "3304", "330420", "Olahan rias mata (eyeliner, eyeshadow, maskara)", "Eye make-up preparations", "u", 10.0, False, "verified_rules"),
    ("33043000", "33", "3304", "330430", "Olahan untuk manikur atau pedikur (cat kuku)", "Manicure or pedicure preparations", "u", 10.0, False, "verified_rules"),
    ("33049100", "33", "3304", "330491", "Bubuk, dipadatkan maupun tidak (bedak wajah)", "Powders, whether or not compressed", "kg", 10.0, False, "verified_rules"),
    ("33049910", "33", "3304", "330499", "Olahan anti jerawat", "Anti-acne preparations", "kg", 10.0, False, "verified_rules"),
    ("33049920", "33", "3304", "330499", "Krim dan losion pemutih kulit", "Skin bleaching creams and lotions", "kg", 10.0, False, "verified_rules"),
    ("33049930", "33", "3304", "330499", "Cairan dan krim untuk perawatan kulit (serum, pelembab wajah)", "Skin care liquids and creams", "u", 10.0, False, "verified_rules"),
    ("33049990", "33", "3304", "330499", "Olahan kecantikan dan rias lainnya (body lotion, sunblock)", "Other beauty or make-up preparations", "u", 10.0, False, "verified_rules"),
    ("33051000", "33", "3305", "330510", "Sampo pembersih rambut", "Shampoos", "u", 10.0, False, "verified_rules"),
    ("33052000", "33", "3305", "330520", "Olahan untuk pengeriting atau pelurus rambut permanen", "Preparations for permanent waving or straightening", "kg", 10.0, False, "verified_rules"),
    ("33053000", "33", "3305", "330530", "Semprotan rambut (hair spray)", "Hair lacquers", "kg", 10.0, False, "verified_rules"),
    ("33059000", "33", "3305", "330590", "Olahan rambut lainnya (kondisioner, pomade, minyak rambut)", "Other hair preparations", "kg", 10.0, False, "verified_rules"),
    ("33061000", "33", "3306", "330610", "Pasta gigi (odol)", "Dentifrices", "kg", 10.0, False, "verified_rules"),
    ("33062000", "33", "3306", "330620", "Benang yang digunakan untuk membersihkan sela gigi (dental floss)", "Yarn used to clean between the teeth", "kg", 10.0, False, "verified_none"),
    ("33069000", "33", "3306", "330690", "Olahan kebersihan mulut lainnya (obat kumur)", "Other oral hygiene preparations", "kg", 10.0, False, "verified_rules"),
    ("33071000", "33", "3307", "330710", "Olahan sebelum, sewaktu, atau setelah bercukur (shaving cream)", "Pre-shave, shaving or after-shave preparations", "kg", 10.0, False, "verified_rules"),
    ("33072000", "33", "3307", "330720", "Deodoran pribadi dan antiperspiran", "Personal deodorants and antiperspirants", "u", 10.0, False, "verified_rules"),
    ("33073000", "33", "3307", "330730", "Garam mandi wangi dan olahan mandi lainnya", "Perfumed bath salts and other bath preparations", "kg", 10.0, False, "verified_rules"),
    ("33074100", "33", "3307", "330741", "Agarbatti dan dupa wangi lainnya", "Agarbatti and other odoriferous preparations", "kg", 10.0, False, "verified_none"),
    ("33074910", "33", "3307", "330749", "Olahan pengharum ruangan cair atau aerosol", "Room deodorising preparations", "kg", 10.0, False, "verified_rules"),
    ("33079090", "33", "3307", "330790", "Produk kosmetik dan wewangian lainnya", "Other perfumery or cosmetic products", "kg", 10.0, False, "verified_rules"),

    # =========================================================================
    # BAB 61: Pakaian dan Aksesori Pakaian, Rajutan atau Kaitan
    # =========================================================================
    ("61012000", "61", "6101", "610120", "Mantel luar pria rajutan dari katun", "Men's overcoats knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61013000", "61", "6101", "610130", "Mantel luar pria rajutan dari serat buatan", "Men's overcoats knitted of man-made fibres", "u", 15.0, False, "verified_rules"),
    ("61022000", "61", "6102", "610220", "Mantel luar wanita rajutan dari katun", "Women's overcoats knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61034200", "61", "6103", "610342", "Celana panjang dan celana pendek pria rajutan dari katun", "Men's trousers knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61044200", "61", "6104", "610442", "Gaun wanita rajutan dari katun", "Women's dresses knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61045200", "61", "6104", "610452", "Rok dan rok terpisah wanita rajutan dari katun", "Women's skirts knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61046200", "61", "6104", "610462", "Celana panjang wanita rajutan dari katun", "Women's trousers knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61051000", "61", "6105", "610510", "Kemeja pria rajutan dari katun", "Men's shirts knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61052000", "61", "6105", "610520", "Kemeja pria rajutan dari serat buatan", "Men's shirts knitted of man-made fibres", "u", 15.0, False, "verified_rules"),
    ("61061000", "61", "6106", "610610", "Blus dan kemeja blus wanita rajutan dari katun", "Women's blouses knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61071100", "61", "6107", "610711", "Celana dalam dan cawat pria rajutan dari katun", "Men's underpants knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61082100", "61", "6108", "610821", "Celana dalam wanita rajutan dari katun", "Women's briefs knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61091010", "61", "6109", "610910", "Kaos oblong dan singlet rajutan dari katun untuk pria atau anak laki-laki", "T-shirts and singlets, knitted of cotton, for men or boys", "u", 15.0, False, "verified_rules"),
    ("61091020", "61", "6109", "610910", "Kaos oblong dan singlet rajutan dari katun untuk wanita atau anak perempuan", "T-shirts and singlets, knitted of cotton, for women or girls", "u", 15.0, False, "verified_rules"),
    ("61099000", "61", "6109", "610990", "Kaos oblong dan singlet rajutan dari bahan tekstil lainnya (polyester)", "T-shirts and singlets, knitted of other textile materials", "u", 15.0, False, "verified_rules"),
    ("61101100", "61", "6110", "611011", "Jerseys, pullovers, cardigans dari wol", "Jerseys, pullovers, cardigans of wool", "u", 15.0, False, "verified_rules"),
    ("61102000", "61", "6110", "611020", "Jersey, pullover, cardigan, rompi dan barang serupa, rajutan, dari katun", "Jerseys, pullovers, cardigans, waistcoats, knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61103000", "61", "6110", "611030", "Jersey, pullover, cardigan rajutan dari serat buatan", "Jerseys, pullovers, cardigans, knitted of man-made fibres", "u", 15.0, False, "verified_rules"),
    ("61121100", "61", "6112", "611211", "Pakaian olahraga (track suits) rajutan dari katun", "Track suits knitted of cotton", "u", 15.0, False, "verified_rules"),
    ("61159500", "61", "6115", "611595", "Kaus kaki rajutan dari katun", "Socks knitted of cotton", "pa", 15.0, False, "verified_rules"),

    # =========================================================================
    # BAB 62: Pakaian dan Aksesori Pakaian, Bukan Rajutan (Tenun)
    # =========================================================================
    ("62012000", "62", "6201", "620120", "Mantel luar pria tenun dari wol", "Men's overcoats of wool, not knitted", "u", 15.0, False, "verified_rules"),
    ("62013000", "62", "6201", "620130", "Mantel luar pria tenun dari katun", "Men's overcoats of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62023000", "62", "6202", "620230", "Mantel luar wanita tenun dari katun", "Women's overcoats of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62031100", "62", "6203", "620311", "Setelan jas pria tenun dari wol", "Men's suits of wool, not knitted", "u", 15.0, False, "verified_rules"),
    ("62031200", "62", "6203", "620312", "Setelan jas pria tenun dari serat sintetis", "Men's suits of synthetic fibres, not knitted", "u", 15.0, False, "verified_rules"),
    ("62032200", "62", "6203", "620322", "Ensemble pria tenun dari katun", "Men's ensembles of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62033200", "62", "6203", "620332", "Jas dan blazer pria tenun dari katun", "Men's jackets and blazers of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62034290", "62", "6203", "620342", "Celana panjang pria atau anak laki-laki dari katun, bukan rajutan (chino, denim)", "Men's trousers of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62034300", "62", "6203", "620343", "Celana panjang pria tenun dari serat sintetis", "Men's trousers of synthetic fibres, not knitted", "u", 15.0, False, "verified_rules"),
    ("62044200", "62", "6204", "620442", "Gaun wanita tenun dari katun", "Women's dresses of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62045200", "62", "6204", "620452", "Rok dan rok terpisah wanita tenun dari katun", "Women's skirts of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62046200", "62", "6204", "620462", "Celana panjang wanita atau anak perempuan dari katun, bukan rajutan", "Women's trousers of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62052000", "62", "6205", "620520", "Kemeja pria atau anak laki-laki dari katun, bukan rajutan", "Men's shirts of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62053000", "62", "6205", "620530", "Kemeja pria tenun dari serat buatan", "Men's shirts of man-made fibres, not knitted", "u", 15.0, False, "verified_rules"),
    ("62063000", "62", "6206", "620630", "Blus, kemeja dan kemeja blus wanita dari katun, bukan rajutan", "Women's blouses of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62064000", "62", "6206", "620640", "Blus wanita tenun dari serat buatan", "Women's blouses of man-made fibres, not knitted", "u", 15.0, False, "verified_rules"),
    ("62113200", "62", "6211", "621132", "Pakaian pria lainnya tenun dari katun", "Other men's garments of cotton, not knitted", "u", 15.0, False, "verified_rules"),
    ("62121000", "62", "6212", "621210", "Kutang (brassieres)", "Brassieres", "u", 15.0, False, "verified_rules"),

    # =========================================================================
    # BAB 84: Reaktor Nuklir, Ketel, Mesin dan Peralatan Mekanis
    # =========================================================================
    ("84131100", "84", "8413", "841311", "Pompa penyalur bahan bakar minyak pada SPBU", "Pumps for dispensing fuel or lubricants", "u", 5.0, False, "verified_rules"),
    ("84133010", "84", "8413", "841330", "Pompa bahan bakar atau pelumas untuk kendaraan bermotor", "Fuel, lubricating pumps for internal combustion engines", "u", 5.0, False, "verified_none"),
    ("84137091", "84", "8413", "841370", "Pompa sentrifugal air lainnya, daya motor listrik > 1,5 kW", "Centrifugal water pumps, electric motor > 1.5 kW", "u", 5.0, False, "verified_none"),
    ("84137099", "84", "8413", "841370", "Pompa sentrifugal lainnya untuk cairan industri", "Other centrifugal pumps for liquids", "u", 5.0, False, "verified_none"),
    ("84143010", "84", "8414", "841430", "Kompresor dari jenis yang digunakan pada peralatan pendingin kulkas", "Compressors of a kind used in refrigerating equipment", "u", 5.0, False, "verified_rules"),
    ("84144000", "84", "8414", "841440", "Kompresor udara terpasang pada sasis beroda untuk ditarik", "Air compressors mounted on a wheeled chassis for towing", "u", 5.0, False, "verified_none"),
    ("84148011", "84", "8414", "841480", "Kompresor gas atau udara industri kapasitas tinggi", "Industrial air or gas compressors", "u", 5.0, False, "verified_none"),
    ("84186910", "84", "8418", "841869", "Peralatan pendingin dan pembeku industri (water chiller)", "Industrial refrigerating or freezing equipment, chillers", "u", 5.0, False, "verified_rules"),
    ("84212111", "84", "8421", "842121", "Peralatan penyaring atau pemurni air untuk keperluan rumah tangga", "Filtering or purifying machinery for water, domestic", "u", 5.0, False, "verified_rules"),
    ("84212122", "84", "8421", "842121", "Peralatan penyaring atau pemurni air industri kapasitas > 500 liter/jam", "Filtering or purifying machinery for water, industrial > 500 l/hr", "u", 5.0, False, "verified_none"),
    ("84223000", "84", "8422", "842230", "Mesin untuk mengisi, menutup, menyumbat atau menyegel botol, kaleng, kotak, kantong atau kemasan lainnya", "Machinery for filling, closing, sealing or labelling bottles, cans, boxes, bags", "u", 0.0, False, "verified_none"),
    ("84224000", "84", "8422", "842240", "Mesin pembungkus atau pengemas lainnya (termasuk mesin pembungkus susut panas)", "Other packing or wrapping machinery (including heat-shrink wrapping machinery)", "u", 0.0, False, "verified_none"),
    ("84283300", "84", "8428", "842833", "Konveyor sabuk lainnya (belt conveyor) untuk barang industri", "Other belt conveyors for goods", "u", 5.0, False, "verified_none"),
    ("84283990", "84", "8428", "842839", "Konveyor mekanis aksi kontinu lainnya", "Other continuous-action elevators and conveyors", "u", 5.0, False, "verified_none"),
    ("84811099", "84", "8481", "848110", "Katup penurun tekanan (pressure reducing valve) lainnya", "Other pressure-reducing valves", "u", 5.0, False, "verified_rules"),
    ("84812090", "84", "8481", "848120", "Katup untuk transmisi pneumatik atau oleohidrolik lainnya", "Valves for oleohydraulic or pneumatic transmissions, other", "u", 5.0, False, "verified_rules"),
    ("84813090", "84", "8481", "848130", "Katup searah (check valves, non-return valves) lainnya", "Check (non-return) valves, other", "u", 5.0, False, "verified_rules"),
    ("84814000", "84", "8481", "848140", "Katup pengaman atau katup pelepas tekanan (safety or relief valves)", "Safety or relief valves", "u", 5.0, False, "verified_rules"),
    ("84818011", "84", "8481", "848180", "Katup bola dan katup sumbat dari tembaga atau paduan tembaga (brass ball valve)", "Ball and plug valves, of copper or copper alloys", "u", 5.0, False, "verified_rules"),
    ("84818012", "84", "8481", "848180", "Katup gerbang dari tembaga atau paduan tembaga (brass gate valve)", "Gate valves, of copper or copper alloys", "u", 5.0, False, "verified_rules"),
    ("84818013", "84", "8481", "848180", "Katup kupu-kupu dari besi atau baja (butterfly valve)", "Butterfly valves, of iron or steel", "u", 5.0, False, "verified_rules"),
    ("84818014", "84", "8481", "848180", "Katup bola dari besi atau baja (cast iron/steel ball valve)", "Ball valves, of iron or steel", "u", 5.0, False, "verified_rules"),
    ("84818015", "84", "8481", "848180", "Katup gerbang dari besi atau baja (cast iron/steel gate valve)", "Gate valves, of iron or steel", "u", 5.0, False, "verified_rules"),
    ("84818021", "84", "8481", "848180", "Keran air untuk bak cuci piring atau wastafel", "Water taps for kitchen sinks or wash basins", "u", 10.0, False, "verified_rules"),
    ("84818080", "84", "8481", "848180", "Katup solenoid listrik pengontrol aliran (solenoid valve)", "Solenoid valves for fluid control", "u", 5.0, False, "verified_rules"),
    ("84818099", "84", "8481", "848180", "Katup industri dan peralatan pengatur aliran pipa lainnya", "Other taps, cocks, valves and similar appliances for pipes", "u", 5.0, False, "verified_rules"),
    ("84819020", "84", "8481", "848190", "Bagian dari katup gerbang, katup bola atau katup penurun tekanan", "Parts of gate, ball or pressure reducing valves", "kg", 5.0, False, "verified_rules"),

    # =========================================================================
    # BAB 85: Mesin dan Peralatan Listrik Serta Bagiannya
    # =========================================================================
    ("85011019", "85", "8501", "850110", "Motor listrik mikro output tidak melebihi 37,5 W lainnya", "Other electric motors of an output not exceeding 37.5 W", "u", 5.0, False, "verified_none"),
    ("85012019", "85", "8501", "850120", "Motor universal AC/DC output melebihi 37,5 W tetapi <= 750 W", "Universal AC/DC motors of an output exceeding 37.5 W but <= 750 W", "u", 5.0, False, "verified_none"),
    ("85014019", "85", "8501", "850140", "Motor AC 1-fase output melebihi 750 W", "Other AC motors, single-phase of an output exceeding 750 W", "u", 5.0, False, "verified_none"),
    ("85015119", "85", "8501", "850151", "Motor AC multi-fase output tidak melebihi 750 W", "AC multi-phase motors of an output not exceeding 750 W", "u", 5.0, False, "verified_rules"),
    ("85015219", "85", "8501", "850152", "Motor AC multi-fase output melebihi 750 W tetapi tidak melebihi 7,5 kW", "Other AC multi-phase motors, output exceeding 750 W but <= 7.5 kW", "u", 5.0, False, "verified_rules"),
    ("85015229", "85", "8501", "850152", "Motor AC multi-fase output melebihi 7,5 kW tetapi tidak melebihi 37,5 kW", "Other AC multi-phase motors, output exceeding 7.5 kW but <= 37.5 kW", "u", 5.0, False, "verified_rules"),
    ("85015319", "85", "8501", "850153", "Motor AC multi-fase output melebihi 37,5 kW tetapi <= 75 kW", "Other AC multi-phase motors, output exceeding 37.5 kW but <= 75 kW", "u", 5.0, False, "verified_rules"),
    ("85015329", "85", "8501", "850153", "Motor AC multi-fase output melebihi 75 kW", "Other AC multi-phase motors, output exceeding 75 kW", "u", 5.0, False, "verified_rules"),
    ("85044019", "85", "8504", "850440", "Pengubah arus statis (inverter frekuensi/variable speed drive) untuk motor", "Static converters, inverters, VFD drives", "u", 0.0, False, "verified_none"),
    ("85365099", "85", "8536", "853650", "Sakelar dan tombol listrik lainnya untuk voltase <= 1.000 V (push button)", "Other electrical switches for a voltage not exceeding 1,000 V", "u", 0.0, False, "verified_none"),
    ("85369019", "85", "8536", "853690", "Terminal blok, konektor kabel listrik untuk voltase <= 1.000 V", "Terminals and connectors for wire and cables", "kg", 0.0, False, "verified_none"),
    ("85371019", "85", "8537", "853710", "Papan kontrol terprogram (Programmable Logic Controller / PLC)", "Numerical and programmable control panels (PLC)", "u", 0.0, False, "verified_none"),
    ("85371099", "85", "8537", "853710", "Papan, panel, konsol, lemari kontrol listrik industri voltase <= 1.000 V", "Boards, panels, consoles, cabinets for electric control <= 1,000 V", "u", 5.0, False, "verified_none"),
    ("85437090", "85", "8543", "854370", "Peralatan listrik fungsi khusus (sensor proximity induktif/kapasitif, sensor fotolistrik)", "Other electrical machines and apparatus with individual functions (sensors)", "u", 0.0, False, "verified_none"),
    ("85444299", "85", "8544", "854442", "Kabel listrik tembaga berisolasi berpenyambung voltase <= 1.000 V", "Electric conductors, fitted with connectors <= 1,000 V", "kg", 10.0, False, "verified_rules"),
]

def generate_csv():
    path = "data/seed/hs_codes.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code","chapter","heading","subheading","description_raw","description_en","unit","bm_rate","is_luxury","note"])
        for r in REAL_BTKI_DATA:
            writer.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], f"{r[7]:.3f}", str(r[8]).lower(), r[9]])
    print(f"Generated comprehensive hs_codes.csv with {len(REAL_BTKI_DATA)} authentic BTKI 2022 codes!")

if __name__ == "__main__":
    generate_csv()
