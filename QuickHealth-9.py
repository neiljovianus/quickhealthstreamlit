import streamlit as st
import numpy as np
import plotly.express as px

st.set_page_config(page_title="QuickHealth", layout="wide")

# ---------------- Helpers ----------------
def calc_bmi(weight, height_cm):
    try:
        w = float(weight)
        h = float(height_cm) / 100.0
        if w <= 0 or h <= 0:
            return 0.0
        return w / (h * h)
    except:
        return 0.0

def bmi_category(bmi):
    if bmi == 0:
        return "N/A"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"

def calc_bmr(gender, weight, height_cm, age):
    try:
        w = float(weight); h = float(height_cm); a = int(age)
    except:
        return 0.0
    if w <= 0 or h <= 0 or a <= 0:
        return 0.0
    # Harris-Benedict simplified
    if gender == "Laki-laki":
        return 88.362 + 13.397*w + 4.799*h - 5.677*a
    if gender == "Perempuan":
        return 447.593 + 9.247*w + 3.098*h - 4.330*a
    return 0.0

def activity_factor(gaya, olahraga_per_month):
    base = {"Pasif": 1.2, "Cukup aktif": 1.35, "Aktif": 1.55}.get(gaya, 1.2)
    mod = {"":0, "Tidak pernah":0, "1–3x":0.05, "4–8x":0.12, ">8x":0.20}.get(olahraga_per_month, 0)
    return base + mod

def water_need_l(weight):
    try:
        w = float(weight)
    except:
        return 0.0
    if w <= 0: return 0.0
    # 30-35 ml/kg ~ use 35 ml/kg
    return round((35 * w) / 1000, 2)

# standardized mapping for scores (0-100)
MAP = {
    # ====== POLA MAKAN ======
    # Makan utama per hari
    "≤2x": 45, "3x": 100, "≥3x": 80,
    # Fast food per minggu
    "≤1x/minggu": 100, "2–3x/minggu": 65, "≥3x/minggu": 30,
    # Konsumsi sayur/buah per minggu
    "≤7x": 30, "7–14x": 80, "≥14x": 100,
    # Minuman manis per minggu
    "≤1x/minggu": 100, "2–4x/minggu": 70, "≥4x/minggu": 35,
    # Air putih per hari
    "≤1L": 25, "1–2L": 75, "≥2L": 100,
    # Jarak makan terakhir sebelum tidur
    "≤2 jam": 35, "2–3 jam": 75, "≥3 jam": 100,

    # ====== POLA TIDUR ======
    # Durasi tidur malam
    "≤6 jam": 25, "6–8 jam": 100, "≥8 jam": 80,
    # Konsistensi tidur
    "Tidak teratur": 35, "Cukup teratur": 80, "Teratur": 100,
    # Tidur siang rata-rata
    "Tidak pernah": 90, "≤1 jam/hari": 100, "1–2 jam/hari": 80,
    # Kondisi saat bangun
    "Sangat lelah": 10, "Lelah": 35, "Netral": 65, "Cukup segar": 90, "Sangat segar": 100,

    # ====== AKTIVITAS FISIK ======
    # Olahraga per bulan
    "Tidak pernah": 25, "1–3x": 65, "4–8x": 85, "≥8x": 100,
    # Gaya hidup
    "Pasif (jarang bergerak)": 45, "Cukup aktif (kadang olahraga)": 80, "Aktif (sering bergerak)": 100,
    # Langkah harian
    "≤3000": 25, "3000–7000": 75, "≥7000": 100,

    # ====== KESEHARIAN & MENTAL ======
    # Screen time per hari
    "≤4 jam": 100, "4–6 jam": 70, "≥6 jam": 35,
    # Stres
    "Santai": 100, "Cukup tenang": 90, "Normal": 70, "Sedikit tertekan": 45, "Sangat stres": 25,
    # Mood
    "Buruk": 30, "Kurang": 55, "Netral": 70, "Baik": 90, "Sangat baik": 100,
    # Rokok & Alkohol
    "Tidak pernah": 100, "≤1x/bulan": 80, "1–3x/bulan": 45, "≥1x/minggu": 20,
}


def score_from_map(key):
    return MAP.get(key, 50)


def build_scores(inputs):
    # 4 kategori utama
    w = {
        "makan": 0.35,     # total pola makan (dominant)
        "tidur": 0.25,     # kualitas & durasi
        "aktivitas": 0.25, # langkah, olahraga, screen
        "mental": 0.15     # stres & mood
    }

    # ===== POLA MAKAN =====
    makan_freq = score_from_map(inputs["makan_freq"])
    sayur = score_from_map(inputs["sayur"])
    sweet = score_from_map(inputs["manis"])
    fastfood = score_from_map(inputs["fast_food"])
    air = score_from_map(inputs["air"])
    makan = int(
        (0.25 * makan_freq) +
        (0.25 * sayur) +
        (0.20 * sweet) +
        (0.20 * fastfood) +
        (0.10 * air)
    )

    # ===== TIDUR =====
    sleep_dur = score_from_map(inputs["tidur_durasi"])
    sleep_reg = score_from_map(inputs["tidur_konsistensi"])
    sleep_quality = score_from_map(inputs["tidur_quality"])
    makan_sebelum_tidur = score_from_map(inputs["makan_tidur"])
    tidur = int(
        (0.4 * sleep_dur) +
        (0.25 * sleep_reg) +
        (0.25 * sleep_quality) +
        (0.10 * makan_sebelum_tidur)
    )

    # ===== AKTIVITAS =====
    langkah = score_from_map(inputs["langkah"])
    olahraga = score_from_map(inputs["olahraga"])
    screen = score_from_map(inputs["screen"])
    aktivitas = int(
        (0.5 * langkah) +
        (0.3 * olahraga) +
        (0.2 * screen)
    )

    # ===== MENTAL =====
    stres_penalty = max(0, (inputs["stres_level"] - 3) * 8)
    mood_score = (inputs["mood_level"] - 3) * 5 + 75
    mental = int(min(100, max(0, mood_score - stres_penalty)))

    # ===== OVERALL =====
    overall = (
        w["makan"] * (makan / 100) +
        w["tidur"] * (tidur / 100) +
        w["aktivitas"] * (aktivitas / 100) +
        w["mental"] * (mental / 100)
    ) * 100
    overall = int(min(100, max(0, round(overall))))

    breakdown = {
        "Pola Makan": makan,
        "Pola Tidur": tidur,
        "Aktivitas Fisik": aktivitas,
        "Keseharian & Mental": mental
    }

    return overall, breakdown


def risk_flags(inputs, bmi):
    flags = []
    if bmi >= 25:
        flags.append("Risiko kelebihan berat badan (BMI tinggi).")
    if inputs["tidur_durasi"] == "<6 jam" or inputs["tidur_quality"] in ("Sangat lelah", "Lelah"):
        flags.append("Risiko kurang tidur atau kualitas tidur rendah.")
    if inputs["olahraga"] == "Tidak pernah" and inputs["langkah"] == "<3000":
        flags.append("Risiko kurang aktivitas fisik.")
    if MAP.get(inputs["air"], 50) <= 40:
        flags.append("Risiko dehidrasi ringan.")
    if inputs["stres_level"] >= 4:
        flags.append("Tanda stres relatif tinggi.")
    if inputs["fast_food"] == "Sering (>3x/minggu)":
        flags.append("Konsumsi fast food sering: risiko nutrisi kurang ideal.")
    return flags


def advices(inputs, bmi, score, flags):
    adv = []
    if inputs["tidur_durasi"] == "<6 jam":
        adv.append("Usahakan tidur minimal 6–7 jam; tambah 30–60 menit bertahap.")
    if inputs["tidur_konsistensi"] == "Tidak teratur":
        adv.append("Buat jadwal tidur konsisten (bangun & tidur di waktu sama).")
    if inputs["olahraga"] == "Tidak pernah":
        adv.append("Mulai aktivitas ringan 3x/minggu (jalan 20–30 menit).")
    if inputs["langkah"] == "<3000":
        adv.append("Naikkan target langkah ke >3000/hari, lalu ke 7000.")
    if inputs["air"] == "<1L":
        adv.append("Tambahkan asupan air sampai ~1.5–2L/hari.")
    if inputs["fast_food"] == "Sering (>3x/minggu)":
        adv.append("Kurangi frekuensi fast food; pilih sumber protein + sayur.")
    if bmi >= 25:
        adv.append("Pertimbangkan defisit kalori kecil dan lebih banyak aktivitas.")
    if inputs["stres_level"] >= 4:
        adv.append("Coba teknik relaksasi 10 menit/hari (napas, jalan santai).")

    seen = []
    for a in adv:
        if a not in seen:
            seen.append(a)
    return seen[:6]


# --------------- UI ---------------

# ================= HEADER =================
st.markdown(
    """
    <style>
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 1rem 0.3rem 1rem;
    }
    .left-section {
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    .title {
        font-size: 4.8rem;
        font-weight: 800;
        color: #fff;
    }
    .right-buttons {
        display: flex;
        gap: 0.4rem;
        align-items: flex-end;
    }
    .right-buttons button {
        background-color: transparent;
        border: 1px solid #ddd;
        border-radius: 6px;
        padding: 0.3rem 0.8rem;
        cursor: pointer;
        transition: 0.2s;
    }
    .right-buttons button:hover {
        background-color: #f0f0f0;
    }
    </style>

    <div class="header">
        <div class="left-section">
            <div class="title">🩺QuickHealth</div>
        </div>
        <div class="right-buttons">
            <button onclick="alert('💬 Chatbot — Coming soon!')">💬 Chatbot</button>
            <button onclick="alert('🧑‍⚕️ Konsultasi Dokter — Coming soon!')">🧑‍⚕️ Konsultasi</button>
            <button onclick="alert('💊 Apotek Online — Coming soon!')">💊 Apotek</button>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


with st.form("form_main", clear_on_submit=False):

    st.header("1. Data Dasar")
    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        umur = st.number_input("Umur (tahun)", min_value=0, max_value=120, value=0, step=1, format="%d")
    with c2:
        gender = st.radio("Gender", options=["Laki-laki", "Perempuan"], horizontal=True)
    with c3:
        tinggi = st.number_input("Tinggi (cm)", min_value=0, max_value=250, value=0, step=1, format="%d")
    with c4:
        berat = st.number_input("Berat (kg)", min_value=0, max_value=300, value=0, step=1, format="%d")

    st.markdown("### 2. Pola Makan")
    m1, m2, m3 = st.columns(3)
    with m1:
        makan_freq = st.radio("Makan utama per hari", ["≤2x", "3x", "≥3x"])
        fast_food = st.radio("Fast food per minggu", ["≤1x/minggu", "2–3x/minggu", "≥3x/minggu"])
    with m2:
        sayur = st.radio("Konsumsi sayur/buah per minggu", ["≤7x", "7–14x", "≥14x"])
        manis = st.radio("Minuman manis per minggu", ["≤1x/minggu", "2–4x/minggu", "≥4x/minggu"])
    with m3:
        air = st.radio("Air putih per hari", ["≤1L", "1–2L", "≥2L"])
        makan_tidur = st.radio("Jarak makan terakhir sebelum tidur", ["≤2 jam", "2–3 jam", "≥3 jam"])

    st.markdown("### 3. Pola Tidur")
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        tidur_durasi = st.radio("Durasi tidur malam", ["≤6 jam", "6–8 jam", "≥8 jam"])
    with t2:
        tidur_konsistensi = st.radio("Konsistensi tidur", ["Tidak teratur", "Cukup teratur", "Teratur"])
    with t3:
        tidur_siang = st.radio("Tidur siang rata-rata", ["Tidak pernah", "≤1 jam/hari", "1–2 jam/hari"])
    with t4:
        tidur_quality = st.radio("Kondisi saat bangun", ["Sangat lelah", "Lelah", "Netral", "Cukup segar", "Sangat segar"])

    st.markdown("### 4. Aktivitas Fisik")
    a1, a2, a3 = st.columns(3)
    with a1:
        olahraga = st.radio("Olahraga per bulan", ["Tidak pernah", "1–3x", "4–8x", "≥8x"])
    with a2:
        gaya = st.radio("Gaya hidup", ["Pasif (jarang bergerak)", "Cukup aktif (kadang olahraga)", "Aktif (sering bergerak)"])
    with a3:
        langkah = st.radio("Langkah harian", ["≤3000", "3000–7000", "≥7000"])

    st.markdown("### 5. Keseharian & Mental")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        screen = st.radio("Screen time per hari", ["≤4 jam", "4–6 jam", "≥6 jam"])
    with k2:
        stres_label = st.radio("Seberapa stres akhir-akhir ini", ["Santai", "Cukup tenang", "Normal", "Sedikit tertekan", "Sangat stres"])
        stres_map = {"Santai":1, "Cukup tenang":2, "Normal":3, "Sedikit tertekan":4, "Sangat stres":5}
        stres_level = stres_map.get(stres_label, 3)
    with k3:
        mood_label = st.radio("Rata-rata mood seminggu", ["Buruk", "Kurang", "Netral", "Baik", "Sangat baik"])
        mood_map = {"Buruk":1, "Kurang":2, "Netral":3, "Baik":4, "Sangat baik":5}
        mood_level = mood_map.get(mood_label, 3)
    with k4:
        rokok = st.radio("Rokok", ["Tidak pernah", "≤1x/bulan", "1–3x/bulan", "≥1x/minggu"])
        alkohol = st.radio("Alkohol", ["Tidak pernah", "≤1x/bulan", "1–3x/bulan", "≥1x/minggu"])

    submitted = st.form_submit_button("🚀 Proses & Tampilkan Hasil")


# --------------- Processing & Output ---------------
if submitted:
    problems = []
    if umur <= 0: problems.append("Umur harus diisi (>0).")
    if not gender or gender not in ["Laki-laki", "Perempuan"]: problems.append("Pilih gender.")
    if tinggi <= 0: problems.append("Tinggi harus diisi (>0).")
    if berat <= 0: problems.append("Berat harus diisi (>0).")

    if problems:
        st.error("Input tidak lengkap:\n- " + "\n- ".join(problems))
    else:
        inputs = {
            "makan_freq": makan_freq, "fast_food": fast_food, "sayur": sayur, "manis": manis,
            "air": air, "makan_tidur": makan_tidur,
            "tidur_durasi": tidur_durasi, "tidur_konsistensi": tidur_konsistensi,
            "tidur_siang": tidur_siang, "tidur_quality": tidur_quality,
            "olahraga": olahraga, "gaya": gaya, "langkah": langkah,
            "screen": screen, "stres_level": stres_level, "mood_level": mood_level,
            "rokok": rokok, "alkohol": alkohol
        }

        bmi = calc_bmi(berat, tinggi)
        bmi_cat = bmi_category(bmi)
        bmr = calc_bmr(gender, berat, tinggi, umur)
        af = activity_factor(gaya if gaya!="" else "Pasif", olahraga)
        tdee = bmr * af if bmr>0 else 0.0
        water_need = water_need_l(berat)
        health_score, breakdown = build_scores(inputs)
        flags = risk_flags(inputs, bmi)
        advice = advices(inputs, bmi, health_score, flags)

        # Output layout
        st.markdown("## 📊 Hasil Analisis")
        colL, colR = st.columns([1,1], gap="large")

        with colL:
            st.subheader("Indikator Fisik")
            st.metric("BMI -> Ukuran keseimbangan antara berat dan tinggi badan", f"{bmi:.1f}", bmi_cat)
            st.metric("BMR (kcal/day) -> Jumlah kalori dasar yang dibutuhkan tubuh saat istirahat", f"{bmr:.0f}")
            st.metric("TDEE (est. kcal/day) -> Perkiraan kalori yang digunakan tubuh dalam satu hari", f"{tdee:.0f}")
            st.metric("Kebutuhan air (L/day) -> Jumlah air yang dianjurkan untuk dikonsumsi per hari", f"{water_need:.2f}")

            st.markdown("### Health Score")
            label = "Baik" if health_score>=75 else ("Cukup" if health_score>=45 else "Kurang")
            st.header(f"{health_score}/100 — {label}")

            st.markdown("### Indikasi Risiko")
            if flags:
                for f in flags:
                    st.warning(f)
            else:
                st.success("Tidak ada indikasi risiko utama berdasarkan input.")

        with colR:
            st.subheader("Breakdown per area (0-100)")
            # horizontal bar via plotly
            categories = list(breakdown.keys())
            categories.reverse()
            values = [breakdown[k] for k in categories]
            fig = px.bar(x=values, y=categories, orientation='h',
                         labels={'x':'Skor','y':'Area'}, width=700, height=300)
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_range=[0,100])
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Saran singkat")
            if advice:
                for a in advice:
                    st.write("- " + a)
            else:
                st.write("Tidak ada saran khusus. Pertahankan gaya hidup baik.")

            # st.markdown("---")
            # st.subheader("Ringkasan Kategori")
            # st.write({
            #     "Pola makan": "Baik" if breakdown["Pola Makan"]>=75 else ("Cukup" if breakdown["Pola Makan"]>=45 else "Buruk"),
            #     "Tidur": "Baik" if breakdown["Pola Tidur"]>=75 else ("Cukup" if breakdown["Pola Tidur"]>=45 else "Buruk"),
            #     "Aktivitas": "Aktif" if breakdown["Aktivitas Fisik"]>=75 else ("Cukup" if breakdown["Aktivitas Fisik"]>=45 else "Kurang"),
            #     "Mental": "Stabil" if breakdown["Keseharian & Mental"]>=60 else "Perlu perhatian"
            # })
