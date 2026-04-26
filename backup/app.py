from flask import Flask, render_template, request

app = Flask(__name__)

def diagnosa_toyota(gejala_list):
    hasil = []
    if 'ac tidak dingin' in gejala_list:
        hasil.append("Freon habis")

    if 'mesin tidak mau hidup' in gejala_list:
        hasil.append("Aki lemah atau kabel aki kendor.")

    if 'rem blong' in gejala_list:
        hasil.append("Minyak rem bocor")

    if not hasil:
        hasil.append("Tidak ada diagnosa yang cocok.")

    return list(dict.fromkeys(hasil))

@app.route("/", methods=["GET", "POST"])
def index():
    hasil = []
    selected = []

    gejala_list = [
        'ac tidak dingin', 'mesin tidak mau hidup', 'rem blong'
    ]

    if request.method == "POST":
        selected = request.form.getlist("gejala")
        if selected:
            hasil = diagnosa_toyota(selected)

    return render_template("index.html", hasil=hasil, gejala_list=gejala_list, selected=selected)

if __name__ == "__main__":
    app.run(debug=True)