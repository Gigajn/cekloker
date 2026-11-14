"""Unit test untuk social_signals.py (flag engine CekLoker).

Jalankan:  python3 -m unittest discover -s tests -v
(dari direktori packages/flag-engine)

Ditulis dengan unittest stdlib karena pytest TIDAK tersedia di VM ini
(cek 15 Nov 2026: `python3 -m pytest` -> No module named pytest).
Test-test ini juga jalan di bawah pytest bila nanti tersedia.
"""

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from social_signals import (
    aggregate_signals,
    detect_complaints,
    detect_fee_request,
    score_ghost_job,
    score_news_event,
    score_rating,
    score_recommend_rate,
)

URL = "https://contoh.test/bukti"
D = date(2026, 11, 15)


def reviews(*texts):
    return [{"text": t, "date": D, "url": URL} for t in texts]


class TestScoreRating(unittest.TestCase):
    def test_rating_tinggi_n_besar_poin_penuh(self):
        s = score_rating(4.4, 155, source="glassdoor", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 15)
        self.assertEqual(s.confidence, "high")

    def test_rating_tinggi_n_20_poin_penuh_confidence_medium(self):
        s = score_rating(4.0, 20, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 15)
        self.assertEqual(s.confidence, "medium")

    def test_rating_menengah_n_20(self):
        s = score_rating(3.7, 50, source="glassdoor", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 8)

    def test_rating_rendah_n_20(self):
        s = score_rating(2.4, 30, source="glassdoor", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, -10)

    def test_rating_n_kecil_setengah_poin(self):
        # Brinks (data nyata JobStreet, 15 Nov 2026): 4.8 dari 9 ulasan.
        # Bukan nol — tapi juga bukan poin penuh: n terlalu kecil.
        s = score_rating(4.8, 9, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 8)  # round(15 * 0.5) = round(7.5) = 8
        self.assertEqual(s.confidence, "low")

    def test_rating_n_sangat_kecil_tanpa_poin(self):
        s = score_rating(5.0, 2, source="glassdoor", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)
        self.assertFalse(s.decisive)
        self.assertIn("konteks", s.notes)

    def test_rating_tanpa_bukti_gagal_keras(self):
        with self.assertRaises(ValueError):
            score_rating(4.0, 30, source="glassdoor", evidence_url="", evidence_date=D)

    def test_rating_di_luar_skala_ditolak(self):
        with self.assertRaises(ValueError):
            score_rating(5.5, 30, source="glassdoor", evidence_url=URL, evidence_date=D)


class TestRecommendRate(unittest.TestCase):
    def test_rekomendasi_tinggi(self):
        s = score_recommend_rate(97, 155, source="glassdoor", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 5)

    def test_rekomendasi_rendah(self):
        s = score_recommend_rate(40, 30, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, -5)

    def test_rekomendasi_n_kecil_konteks_saja(self):
        s = score_recommend_rate(100, 4, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)
        self.assertFalse(s.decisive)


class TestDetectComplaints(unittest.TestCase):
    def test_satu_ulasan_ekstrem_tidak_menggerakkan_skor(self):
        # Grill G-3: 1 ulasan marah tidak boleh mengubah skor.
        r = reviews("Gaji telat terus, lembur tidak dibayar, PHK sepihak!")
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)
        self.assertFalse(s.decisive)

    def test_dua_ulasan_juga_belum_cukup(self):
        r = reviews("gaji telat", "gaji telat banget")
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)

    def test_tiga_ulasan_keluhan_ringan(self):
        r = reviews(
            "gaji telat tiap bulan",
            "gaji sering telat",
            "lembur tidak dibayar",
            "lingkungan oke",
            "kerjaan santai",
        )
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, -5)

    def test_lima_ulasan_dan_pangsa_lebih_dari_10_persen(self):
        r = reviews(*(["gaji telat terus"] * 5 + ["kerjaan oke"] * 20))
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, -15)
        self.assertEqual(s.value["gaji_telat_atau_ditahan"], 5)

    def test_lima_ulasan_tapi_pangsa_kecil_tetap_ringan(self):
        # 5 dari 100 ulasan = 5% < 10%: parah secara absolut, tapi
        # pangsa kecil — tetap -5, bukan -15 (grill G-3).
        r = reviews(*(["gaji telat terus"] * 5 + ["kerjaan oke"] * 95))
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, -5)

    def test_satu_ulasan_mengulang_kata_dihitung_sekali(self):
        r = reviews("gaji telat, gaji telat, gaji telat, gaji telat, gaji telat")
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)
        self.assertEqual(s.value["gaji_telat_atau_ditahan"], 1)

    def test_negasi_tidak_dihitung_keluhan(self):
        # "gaji tidak pernah telat" adalah PUJIAN, bukan keluhan (grill G-4).
        r = reviews(
            "gaji tidak pernah telat, lembur selalu dibayar",
            "gaji tidak pernah telat",
            "semuanya oke",
        )
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)
        self.assertEqual(s.value, {})

    def test_negasi_sebelum_kata_kunci_membatalkan(self):
        # Negasi yang berdiri SEBELUM kata kunci harus membatalkan
        # kecocokan — ini yang benar-benar menguji pelindung negasi.
        r = reviews(
            "tidak pernah ada gaji telat di sini",
            "tidak pernah ada gaji telat, semuanya oke",
            "bukan karena gaji telat, saya resign karena pindah kota",
        )
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)
        self.assertEqual(s.value, {})

    def test_kata_harga_tidak_dianggap_negasi(self):
        # "harga" mengandung "ga" — pelindung negasi memakai batas kata,
        # jadi ini tetap keluhan (regresi untuk NEGATION substring).
        r = reviews(
            "dengan harga murah pun gaji telat tetap tidak bisa diterima",
            "gaji telat terus",
            "gaji telat lagi",
        )
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, -5)
        self.assertEqual(s.value["gaji_telat_atau_ditahan"], 3)

    def test_gajinya_telat_terdeteksi(self):
        r = reviews("gajinya telat", "gajinya telat lagi", "gajinya sering telat")
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, -5)

    def test_kutipan_dipotong_280_karakter(self):
        r = reviews("gaji telat " + ("x" * 500))
        s = detect_complaints(r, source="jobstreet_review", evidence_url=URL, evidence_date=D)
        self.assertLessEqual(len(s.evidence_text), 280)


class TestDetectFeeRequest(unittest.TestCase):
    def test_biaya_pendaftaran_terdeteksi_dan_override(self):
        s = detect_fee_request(
            "Silakan transfer biaya pendaftaran Rp300.000 sebelum interview.",
            source="glints", evidence_url=URL, evidence_date=D,
        )
        self.assertTrue(s.red_override)
        self.assertTrue(s.value)

    def test_biaya_training_terdeteksi(self):
        s = detect_fee_request(
            "Kandidat wajib bayar biaya training di awal.",
            source="jobstreet", evidence_url=URL, evidence_date=D,
        )
        self.assertTrue(s.red_override)

    def test_staff_administrasi_bukan_biaya(self):
        # Grill G-5: "staff administrasi" adalah jabatan sah.
        s = detect_fee_request(
            "Dibutuhkan staff administrasi untuk mengelola dokumen kantor.",
            source="glints", evidence_url=URL, evidence_date=D,
        )
        self.assertFalse(s.red_override)
        self.assertFalse(s.value)

    def test_adm_tanpa_konteks_biaya_tidak_terdeteksi(self):
        s = detect_fee_request(
            "Bagian ADM akan menghubungi kandidat terpilih.",
            source="glints", evidence_url=URL, evidence_date=D,
        )
        self.assertFalse(s.red_override)

    def test_tidak_ada_biaya_tidak_terdeteksi(self):
        # Grill G-5: lowongan sah yang menegaskan "tidak ada biaya"
        # tidak boleh memicu override.
        s = detect_fee_request(
            "Tidak ada biaya pendaftaran. Semua proses rekrutmen gratis.",
            source="glints", evidence_url=URL, evidence_date=D,
        )
        self.assertFalse(s.red_override)

    def test_lowongan_normal_tidak_terdeteksi(self):
        s = detect_fee_request(
            "Gaji Rp5-7 juta, BPJS, jam kerja Senin-Jumat.",
            source="glints", evidence_url=URL, evidence_date=D,
        )
        self.assertFalse(s.red_override)


class TestGhostJob(unittest.TestCase):
    def test_ghost_job_tiga_lowongan_basi(self):
        s = score_ghost_job(120, 4, job_title="Backend Engineer",
                            source="glints", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, -10)

    def test_satu_lowongan_basi_konteks_saja(self):
        s = score_ghost_job(120, 1, job_title="Backend Engineer",
                            source="glints", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)

    def test_jabatan_evergreen_tidak_dihukum(self):
        # Grill G-6: lowongan sales memang selalu buka.
        s = score_ghost_job(200, 8, job_title="Sales Executive",
                            source="glints", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)
        self.assertIn("evergreen", s.notes)

    def test_tayang_90_hari_bukan_ghost_job(self):
        s = score_ghost_job(90, 5, job_title="Designer",
                            source="glints", evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)


class TestNewsEvent(unittest.TestCase):
    def test_phk_dua_media_dalam_setahun(self):
        s = score_news_event("layoff_massal", n_outlets=2, within_months=3,
                             evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, -15)

    def test_phk_satu_media_konteks_saja(self):
        # Grill G-7: satu artikel bisa jadi rumor.
        s = score_news_event("layoff_massal", n_outlets=1, within_months=3,
                             evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)

    def test_phk_lebih_dari_setahun_konteks_saja(self):
        s = score_news_event("layoff_massal", n_outlets=3, within_months=18,
                             evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 0)

    def test_ekspansi_dua_media(self):
        s = score_news_event("ekspansi", n_outlets=2, within_months=2,
                             evidence_url=URL, evidence_date=D)
        self.assertEqual(s.points, 5)

    def test_event_tidak_dikenal_ditolak(self):
        with self.assertRaises(ValueError):
            score_news_event("bangkrut", n_outlets=2, within_months=1,
                             evidence_url=URL, evidence_date=D)


class TestAggregate(unittest.TestCase):
    def _signals_perusahaan_bagus(self):
        # Reputasi bagus + ekspansi, tapi HANYA 2 kategori terukur.
        return [
            score_rating(4.4, 155, source="glassdoor", evidence_url=URL, evidence_date=D),
            score_recommend_rate(97, 155, source="glassdoor", evidence_url=URL, evidence_date=D),
            score_news_event("ekspansi", n_outlets=2, within_months=2,
                             evidence_url=URL, evidence_date=D),
        ]

    def test_perusahaan_bagus_tapi_data_sebagian_tidak_langsung_green(self):
        # Grill G-2: reputasi 20/25 + stabilitas 5/20 = 25 poin dari cap
        # terukur 45 -> total ternormalisasi 56 (Mixed), BUKAN Red 25/100
        # seperti pada penjumlahan mentah — dan bukan Green, karena baru
        # 2 dari 5 kategori yang terukur.
        result = aggregate_signals(self._signals_perusahaan_bagus())
        self.assertEqual(result["total"], 56)
        self.assertEqual(result["label"], "Mixed")
        self.assertEqual(result["measured_cap"], 45)

    def test_green_butuh_tiga_kategori_atau_lebih(self):
        # Sinyal transparansi/gaji di sini dibuat langsung sebagai Signal:
        # di produk nyata sinyal itu berasal dari modul lain (tim job-board),
        # bukan dari modul sosial ini.
        from social_signals import Signal
        signals = self._signals_perusahaan_bagus() + [
            Signal(category="transparansi", key="salary_transparency", value=0.9,
                   points=25, evidence_url=URL, evidence_text="", evidence_date=D,
                   source="glints", confidence="high", decisive=True),
            Signal(category="gaji_benefit", key="salary_vs_umr", value=1.3,
                   points=15, evidence_url=URL, evidence_text="", evidence_date=D,
                   source="glints", confidence="high", decisive=True),
        ]
        result = aggregate_signals(signals)
        # (20 + 5 + 25 + 15) / (25 + 20 + 25 + 15) = 65/85 -> 76
        self.assertEqual(result["total"], 76)
        self.assertEqual(result["label"], "Green")

    def test_semua_bukti_dari_satu_kategori_tidak_cukup(self):
        # 3 sinyal penentu tapi semuanya reputasi -> Belum cukup data.
        result = aggregate_signals([
            score_rating(4.4, 155, source="glassdoor", evidence_url=URL, evidence_date=D),
            score_recommend_rate(97, 155, source="glassdoor", evidence_url=URL, evidence_date=D),
            detect_complaints(
                reviews(*(["gaji telat"] * 3 + ["oke"] * 20)),
                source="glassdoor", evidence_url=URL, evidence_date=D),
        ])
        self.assertEqual(result["label"], "Belum cukup data")

    def test_belum_cukup_data_bila_sinyal_kurang_dari_tiga(self):
        result = aggregate_signals([
            score_rating(4.4, 155, source="glassdoor", evidence_url=URL, evidence_date=D),
        ])
        self.assertEqual(result["label"], "Belum cukup data")

    def test_fee_override_jadi_red_walau_skor_tinggi(self):
        signals = self._signals_perusahaan_bagus() + [
            detect_fee_request("bayar biaya pendaftaran Rp500rb",
                               source="glints", evidence_url=URL, evidence_date=D),
        ]
        result = aggregate_signals(signals)
        self.assertTrue(result["red_override"])
        self.assertEqual(result["label"], "Red")
        self.assertEqual(len(result["warnings"]), 1)

    def test_kategori_dijepit_tidak_melebihi_cap(self):
        # Reputasi: rating 15 + recommend 5 + keluhan -15 = 5; total
        # ternormalisasi: 100 * 5 / 25 = 20. Satu kategori -> Belum cukup data.
        signals = [
            score_rating(4.5, 100, source="glassdoor", evidence_url=URL, evidence_date=D),
            score_recommend_rate(90, 100, source="glassdoor", evidence_url=URL, evidence_date=D),
            detect_complaints(
                reviews(*(["gaji telat"] * 10 + ["oke"] * 20)),
                source="glassdoor", evidence_url=URL, evidence_date=D),
        ]
        result = aggregate_signals(signals)
        self.assertLessEqual(result["per_category"]["reputasi"], 25)
        self.assertGreaterEqual(result["per_category"]["reputasi"], -25)
        self.assertEqual(result["per_category"]["reputasi"], 15 + 5 - 15)
        self.assertEqual(result["total"], 20)
        self.assertEqual(result["label"], "Belum cukup data")

    def test_total_dijepit_0_sampai_100(self):
        signals = [
            score_rating(1.5, 100, source="glassdoor", evidence_url=URL, evidence_date=D),
            detect_complaints(
                reviews(*(["gaji telat"] * 10 + ["oke"] * 20)),
                source="glassdoor", evidence_url=URL, evidence_date=D),
            score_news_event("tutup", n_outlets=2, within_months=1,
                             evidence_url=URL, evidence_date=D),
        ]
        result = aggregate_signals(signals)
        self.assertGreaterEqual(result["total"], 0)
        self.assertLessEqual(result["total"], 100)
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["label"], "Red")

    def test_kategori_tidak_dikenal_ditolak(self):
        bad = score_rating(4.0, 30, source="glassdoor", evidence_url=URL, evidence_date=D)
        bad = bad.__class__(**{**bad.__dict__, "category": "tak_dikenal"})
        with self.assertRaises(ValueError):
            aggregate_signals([bad])


if __name__ == "__main__":
    unittest.main()
