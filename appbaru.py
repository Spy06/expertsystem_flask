# Mas kasih nafas dela dong mas :)
from flask import Flask, render_template, request, session, redirect, url_for
from experta import *

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

class Gejala(Fact):
    pass

class DiagnosaPenyakit(KnowledgeEngine):
    def __init__(self):
        super().__init__()
        self.hasil_diagnosa = [] 

    @Rule(AND(OR(Gejala(name='wajah_mencong'), Gejala(name='lengan_kaki_lemah'), Gejala(name='bicara_pelo')), Gejala(name='gejala_membaik_cepat')))
    def tia_rule(self):
        self.hasil_diagnosa.append({"kategori": "TIA", "score": 80, "penyakit": "Transient Ischemic Attack (TIA / Stroke Ringan)", "keyakinan": "80%", "detail": SOLUSI_DB["TIA"], "desc": "Gejala khas stroke muncul namun hilang sepenuhnya dalam waktu singkat (< 24 jam). Ini adalah peringatan kuat akan datangnya stroke besar."})

    @Rule(AND(OR(Gejala(name='wajah_mencong'), Gejala(name='lengan_kaki_lemah'), Gejala(name='bicara_pelo')), OR(Gejala(name='gangguan_penglihatan'), Gejala(name='kesulitan_keseimbangan'))))
    def iskemik_awal(self):
        self.hasil_diagnosa.append({"kategori": "STROKE_ISKEMIK", "score": 85, "penyakit": "Suspek Stroke Iskemik (Penyumbatan)", "keyakinan": "85%", "detail": SOLUSI_DB["STROKE_ISKEMIK"], "desc": "Terdapat kelemahan saraf fokal (wajah, gerak, atau bicara). Segera bawa ke IGD untuk mengejar 'Golden Period' penanganan (kurang dari 4.5 jam)."})

    @Rule(AND(Gejala(name='sakit_kepala_hebat_tiba_tiba'), OR(Gejala(name='muntah_menyemprot'), Gejala(name='penurunan_kesadaran'), Gejala(name='hipertensi_ekstrem'))))
    def hemoragik_kritis(self):
        self.hasil_diagnosa.append({"kategori": "STROKE_HEMORAGIK", "score": 95, "penyakit": "Suspek Stroke Hemoragik (Pendarahan Otak)", "keyakinan": "95% (DARURAT)", "detail": SOLUSI_DB["STROKE_HEMORAGIK"], "desc": "Sakit kepala mendadak seperti tersambar petir disertai muntah/pingsan adalah tanda bahaya pecahnya pembuluh darah otak."})
        
    @Rule(AND(Gejala(name='wajah_mencong'), Gejala(name='lengan_kaki_lemah'), Gejala(name='penurunan_kesadaran')))
    def stroke_berat(self):
        self.hasil_diagnosa.append({"kategori": "STROKE_HEMORAGIK", "score": 100, "penyakit": "Serangan Stroke Berat", "keyakinan": "100% (ICU)", "detail": SOLUSI_DB["STROKE_HEMORAGIK"], "desc": "Terjadi defisit neurologis berat dengan hilangnya kesadaran. Nyawa terancam."})

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

def hitung_separasi(pertanyaan_key):
    if pertanyaan_key in ['wajah_mencong', 'lengan_kaki_lemah', 'bicara_pelo']: return 0.95 
    if pertanyaan_key == 'sakit_kepala_hebat_tiba_tiba': return 0.90
    if pertanyaan_key == 'gejala_membaik_cepat': return 0.85
    if pertanyaan_key == 'penurunan_kesadaran': return 0.80
    
    return 0.5 

def pilih_pertanyaan_terbaik(pertanyaan_terpakai):
    best_q = None
    best_score = -1
    
    pertanyaan_tersedia = [q for q, _ in GEJALA_OPTIONS if q not in pertanyaan_terpakai]

    for q_key in pertanyaan_tersedia:
        score = hitung_separasi(q_key)
        
        if score > best_score:
            best_score = score
            best_q = q_key
            
    if best_q:
        q_text = next((text for key, text in GEJALA_OPTIONS if key == best_q), "Pertanyaan tidak ditemukan")
        return best_q, q_text
    
    return None, None

def jalankan_inferensi(gejala_dijawab):
    """Menjalankan mesin Experta dan memfilter hasilnya berdasarkan aturan Stroke."""
    engine = DiagnosaPenyakit()
    engine.reset()
    
    for g, answer in gejala_dijawab.items():
        if answer:
             engine.declare(Gejala(name=g))
    
    engine.run()
    raw_results = engine.hasil_diagnosa

    best_matches = {}
    for res in raw_results:
        kategori = res['kategori']
        current_score = res['score']

        if kategori not in best_matches or current_score > best_matches[kategori]['score']:
            best_matches[kategori] = res
    
    final_results = list(best_matches.values())
    final_results.sort(key=lambda x: x['score'], reverse=True)
    
    return final_results

@app.route("/", methods=["GET"])
def start_game():
    """Memulai dan mereset game dengan kandidat kategori Stroke."""
    session['gejala_dijawab'] = {}
    session['pertanyaan_terpakai'] = []
    session['kandidat_kategori'] = ['STROKE_ISKEMIK', 'STROKE_HEMORAGIK', 'TIA'] 
    
    return redirect(url_for('akinator_loop'))

@app.route("/game", methods=["GET", "POST"])
def akinator_loop():
    gejala_dijawab = session.get('gejala_dijawab', {})
    pertanyaan_terpakai = session.get('pertanyaan_terpakai', [])
    kandidat_kategori = session.get('kandidat_kategori', ['STROKE_ISKEMIK', 'STROKE_HEMORAGIK', 'TIA'])

    if request.method == "POST":
        pertanyaan_sebelumnya = request.form.get('current_question_key')
        jawaban_raw = request.form.get('answer')
        
        if pertanyaan_sebelumnya and jawaban_raw in ['ya', 'tidak']:
            jawaban_is_true = (jawaban_raw == 'ya')
            gejala_dijawab[pertanyaan_sebelumnya] = jawaban_is_true
            session['gejala_dijawab'] = gejala_dijawab
        
        final_results = jalankan_inferensi(gejala_dijawab)
        
        kategori_terpicu = set(res['kategori'] for res in final_results)
        session['kandidat_kategori'] = list(kategori_terpicu)
        kandidat_kategori = list(kategori_terpicu)

        return redirect(url_for('akinator_loop'))

    if len(kandidat_kategori) == 1 or len(pertanyaan_terpakai) >= len(GEJALA_OPTIONS):
        
        final_results = jalankan_inferensi(gejala_dijawab)
        
        if final_results:
            return render_template("final_result.html", results=final_results)
        else:
            return render_template("final_result.html", results=None)

    question_key, question_text = pilih_pertanyaan_terbaik(pertanyaan_terpakai)
    
    if not question_key:
        return render_template("final_result.html", results=None) 
        
    pertanyaan_terpakai.append(question_key)
    session['pertanyaan_terpakai'] = pertanyaan_terpakai
    
    
    return render_template("akinator_question.html", 
                           question_key=question_key,
                           question_text=question_text,
                           candidates_count=len(kandidat_kategori))

if __name__ == "__main__":
    app.run(debug=True, port=5001)