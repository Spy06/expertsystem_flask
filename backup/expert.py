class Diagnosa:
    def __init__(self, symptoms):
        self.symptoms = symptoms

    def diagnosis(self):
        if 'a' in self.symptoms or 'b' in self.symptoms:
            return "X"
        elif 'c' in self.symptoms or 'd' in self.symptoms:
            return "Y"
        else:
            return "Kurangnya data"

symptoms = input("Masukkan kerusakan (Pisahkan menggunakan koma(,)): ").split(',')
symptoms = [symptom.strip() for symptom in symptoms]

bmw = Diagnosa(symptoms)
result = bmw.diagnosis()
print(f"Hasil: {result}")