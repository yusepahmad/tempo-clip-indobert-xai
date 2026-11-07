DEFINITIONS = {'BENCANA_JERAT': 'ancaman, bencana, perangkap, jerat atau keadaan terjepit sebagai kiasan', 'HEWAN_TUBUH': 'hewan, anatomi, deformasi atau perilaku biologis sebagai kiasan', 'KONSUMSI_TRANSAKSI': 'makanan, jamuan, selera, jual-beli atau pertukaran nilai sebagai kiasan', 'LAINNYA': 'metafora dengan domain sumber selain lima domain metaforis yang disebut', 'MESIN_INFRASTRUKTUR': 'mesin, alat, kendaraan, bangunan atau mekanisme buatan sebagai kiasan', 'NON_METAFORA': 'adegan literal tanpa pemetaan metaforis; benda biasa bukan otomatis metafora', 'PERMAINAN_KONTES': 'permainan, pertandingan, kompetisi atau pertunjukan sebagai kiasan'}

def build_prompt(index, df, descriptions, reasons, classes):
    rules = '\n'.join((f'{code}: {label}: {DEFINITIONS[label]}.' for code, label in zip('ABCDEFG', classes)))
    row = df.iloc[index]
    text = 'Klasifikasikan domain SUMBER metafora sampul Tempo, bukan isu politiknya.\n' + rules + '\nLihat ilustrasi dan konteks berikut.\nDeskripsi: ' + descriptions[index]['deskripsi'][:1200] + '\nSumber dan alasan: ' + ((reasons[index].get('sumber_visual') or '') + ' ' + (reasons[index].get('alasan') or ''))[:800] + '\nJudul dan teks: ' + (row.headline_verified + ' ' + row.supporting_text_verified)[:400] + '\nJawab satu kode A sampai G:'
    return text
