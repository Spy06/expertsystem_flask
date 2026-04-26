from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'kunci-rahasia-akinator-rahasia' 

SOLUSI_DB = {
    "TIA": {
        "penanganan": "Pemeriksaan Medis Segera (Mencegah stroke besar)",
        "diet": "Diet rendah garam, rendah kolesterol/lemak jenuh.",
        "medis": "Pemeriksaan MRI/CT-Scan, obat pengencer darah (Aspirin/Clopidogrel) sesuai resep.",
        "red_flag": "Jika gejala muncul kembali atau menetap >24 jam, segera ke IGD.",
        "image": "ministroke.jpg"
    },
    "STROKE_ISKEMIK": {
        "penanganan": "Darurat Medis / Rawat Inap (Golden Period < 4.5 jam)",
        "diet": "Puasa sementara sampai dilakukan tes fungsi menelan (mencegah tersedak).",
        "medis": "Terapi trombolitik (rt-PA) untuk menghancurkan gumpalan darah jika masuk golden period.",
        "red_flag": "Gejala kelumpuhan memburuk, sulit bernapas.",
        "image": "gambar-stroke-iskemik.webp"
    },
    "STROKE_HEMORAGIK": {
        "penanganan": "ICU / Darurat Medis (Risiko Fatal Tinggi)",
        "diet": "Puasa total (NPO), nutrisi diberikan via infus atau selang NGT.",
        "medis": "Kontrol tekanan darah ketat, evaluasi bedah saraf (kraniotomi) untuk hentikan pendarahan.",
        "red_flag": "Koma, penurunan kesadaran drastis, kejang, pupil tidak merespons.",
        "image": "visualisasi-stroke-hemoragik.webp"
    }
}

GEJALA_OPTIONS = [
    ('wajah_mencong', 'Wajah tampak mencong, asimetris, atau turun sebelah (Face drooping)'),
    ('lengan_kaki_lemah', 'Lengan atau kaki tiba-tiba terasa lemah/lumpuh (biasanya satu sisi tubuh)'),
    ('bicara_pelo', 'Bicara menjadi pelo, cadel, atau kesulitan memahami perkataan orang lain'),
    ('sakit_kepala_hebat_tiba_tiba', 'Sakit kepala yang SANGAT parah dan muncul tiba-tiba tanpa sebab'),
    ('gangguan_penglihatan', 'Tiba-tiba pandangan kabur, ganda, atau gelap pada satu/kedua mata'),
    ('kesulitan_keseimbangan', 'Tiba-tiba pusing berputar hebat (vertigo), hilang keseimbangan, atau sulit berjalan'),
    ('muntah_menyemprot', 'Muntah tiba-tiba menyemprot (proyektil) tanpa didahului rasa mual'),
    ('penurunan_kesadaran', 'Tiba-tiba mengantuk berat, pingsan, atau tidak sadarkan diri'),
    ('gejala_membaik_cepat', 'Semua gejala kelemahan tadi HILANG sepenuhnya dalam waktu kurang dari 24 jam'),
    ('hipertensi_ekstrem', 'Tekanan darah saat ini sangat tinggi (misal: Sistolik > 180 atau Diastolik > 120)'),
    ('kesemutan_sebelah', 'Mati rasa atau kesemutan parah pada separuh badan')
]

def jalankan_inferensi(gejala):
    """Pengganti Experta: Logika manual untuk mencocokkan gejala dengan aturan."""
    hasil = []
    
    fast_gejala = gejala.get('wajah_mencong') or gejala.get('lengan_kaki_lemah') or gejala.get('bicara_pelo')

    if fast_gejala and gejala.get('gejala_membaik_cepat'):
        hasil.append({
            "kategori": "TIA", "score": 80, 
            "penyakit": "TIA (Stroke Ringan)", "keyakinan": "80%", 
            "detail": SOLUSI_DB["TIA"], 
            "desc": "Gejala khas stroke muncul namun hilang sepenuhnya dalam waktu singkat (< 24 jam)."
        })

    if fast_gejala and (gejala.get('gangguan_penglihatan') or gejala.get('kesulitan_keseimbangan')):
        hasil.append({
            "kategori": "STROKE_ISKEMIK", "score": 85, 
            "penyakit": "Suspek Stroke Iskemik", "keyakinan": "85%", 
            "detail": SOLUSI_DB["STROKE_ISKEMIK"], 
            "desc": "Terdapat kelemahan saraf fokal. Segera ke IGD untuk Golden Period (< 4.5 jam)."
        })

    if gejala.get('sakit_kepala_hebat_tiba_tiba') and (gejala.get('muntah_menyemprot') or gejala.get('penurunan_kesadaran') or gejala.get('hipertensi_ekstrem')):
        hasil.append({
            "kategori": "STROKE_HEMORAGIK", "score": 95, 
            "penyakit": "Suspek Stroke Hemoragik", "keyakinan": "95%", 
            "detail": SOLUSI_DB["STROKE_HEMORAGIK"], 
            "desc": "Sakit kepala mendadak disertai muntah/pingsan adalah tanda pendarahan otak."
        })

    if gejala.get('wajah_mencong') and gejala.get('lengan_kaki_lemah') and gejala.get('penurunan_kesadaran'):
        hasil.append({
            "kategori": "STROKE_HEMORAGIK", "score": 100, 
            "penyakit": "Serangan Stroke Berat", "keyakinan": "100%", 
            "detail": SOLUSI_DB["STROKE_HEMORAGIK"], 
            "desc": "Terjadi defisit neurologis berat dengan hilangnya kesadaran."
        })

    hasil.sort(key=lambda x: x['score'], reverse=True)
    return hasil

def pilih_pertanyaan_terbaik(pertanyaan_terpakai):
    pertanyaan_tersedia = [q for q in GEJALA_OPTIONS if q[0] not in pertanyaan_terpakai]
    if not pertanyaan_tersedia:
        return None, None
    return pertanyaan_tersedia[0]

@app.route("/", methods=["GET"])
def start_game():
    session['gejala_dijawab'] = {}
    session['pertanyaan_terpakai'] = []
    return redirect(url_for('akinator_loop'))

@app.route("/game", methods=["GET", "POST"])
def akinator_loop():
    gejala_dijawab = session.get('gejala_dijawab', {})
    pertanyaan_terpakai = session.get('pertanyaan_terpakai', [])

    if request.method == "POST":
        pertanyaan_sebelumnya = request.form.get('current_question_key')
        jawaban_raw = request.form.get('answer')
        
        if pertanyaan_sebelumnya:
            gejala_dijawab[pertanyaan_sebelumnya] = (jawaban_raw == 'ya')
            session['gejala_dijawab'] = gejala_dijawab
        
        final_results = jalankan_inferensi(gejala_dijawab)
        if final_results and (final_results[0]['score'] >= 95 or len(pertanyaan_terpakai) >= len(GEJALA_OPTIONS)):
            return render_template("final_result.html", results=final_results)

    question_key, question_text = pilih_pertanyaan_terbaik(pertanyaan_terpakai)
    
    if not question_key:
        final_results = jalankan_inferensi(gejala_dijawab)
        return render_template("final_result.html", results=final_results)
        
    pertanyaan_terpakai.append(question_key)
    session['pertanyaan_terpakai'] = pertanyaan_terpakai
    
    return render_template("akinator_question.html", 
                           question_key=question_key,
                           question_text=question_text)

if __name__ == "__main__":
    app.run(debug=True)