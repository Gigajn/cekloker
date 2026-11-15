import Link from "next/link";

export const metadata = {
  title: "Cara kami menilai — CekLoker",
};

export default function CaraMenilai() {
  return (
    <div className="space-y-6 text-sm leading-relaxed text-slate-700">
      <h1 className="text-2xl font-bold text-slate-900">Cara kami menilai</h1>
      <p>
        CekLoker memberi ringkasan sinyal publik tentang perusahaan — bukan
        vonis, bukan penilaian hukum, dan bukan jaminan. Halaman ini
        menjelaskan rubriknya secara terbuka supaya siapa pun bisa memeriksa
        cara kerja kami, termasuk perusahaan yang dinilai.
      </p>

      <section>
        <h2 className="text-lg font-semibold text-slate-900">1. Rubrik skor (0–100)</h2>
        <p className="mt-1">
          Skor dihitung per kategori, dengan batas (cap) tiap kategori supaya
          satu kategori tidak mendominasi:
        </p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li><strong>Transparansi lowongan — 25 poin.</strong> Gaji dicantumkan, deskripsi tugas jelas, lokasi dan tipe kerja jelas, tidak meminta biaya.</li>
          <li><strong>Reputasi &amp; ulasan — 25 poin.</strong> Rating dan jumlah ulasan, rasio rekomendasi, keluhan yang berulang.</li>
          <li><strong>Stabilitas &amp; legalitas — 20 poin.</strong> Umur perusahaan, terdaftar resmi, berita PHK massal atau penutupan.</li>
          <li><strong>Praktik rekrutmen — 15 poin.</strong> Status lowongan diperbarui rutin; lowongan &ldquo;hantu&rdquo; yang tayang berbulan-bulan tanpa hiring.</li>
          <li><strong>Gaji &amp; benefit — 15 poin.</strong> Gaji dibanding UMR/pasar, BPJS disebut, benefit jelas.</li>
        </ul>
        <p className="mt-2">
          Satu pengecualian penting: <strong>permintaan biaya</strong> yang
          terbukti di teks lowongan langsung membuat label jadi{" "}
          <strong>Red</strong> beserta peringatan — poin positif lain tidak
          bisa &ldquo;menebus&rdquo;nya.
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-slate-900">2. Normalisasi — kenapa skor bukan penjumlahan mentah</h2>
        <p className="mt-1">
          Skor total dihitung hanya dari kategori yang <em>sudah terukur</em>:
        </p>
        <p className="mt-2 rounded-lg bg-slate-100 px-4 py-3 font-mono text-xs sm:text-sm">
          total = 100 × (poin yang diperoleh) / (cap kategori yang terukur)
        </p>
        <p className="mt-2">
          Contoh: perusahaan yang baru terukur reputasi dan stabilitas (cap
          45) dengan perolehan 25 poin mendapat skor 56 (Mixed) — bukan 25
          (Red). Data yang belum diukur tidak boleh disamakan dengan data
          buruk. Label diberikan bila ada minimal <strong>3 sinyal penentu
          dari 2 kategori berbeda</strong>; di bawah itu labelnya{" "}
          <strong>&ldquo;Belum cukup data&rdquo;</strong> — dan itu jawaban yang
          sah, bukan label buruk.
        </p>
        <p className="mt-2">
          Label: <strong>Green 70–100</strong>, <strong>Mixed 40–69</strong>,{" "}
          <strong>Red 0–39</strong>. Ambang ini adalah heuristik yang wajib
          dikalibrasi ulang setelah 50 perusahaan pertama dinilai — bukan
          standar industri.
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-slate-900">3. Sumber bukti</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li><strong>Lowongan:</strong> Glints, Kalibrr, dan halaman karier perusahaan (ATS: Greenhouse, Lever, Ashby, Workable, dsb.).</li>
          <li><strong>Ulasan:</strong> entri manual dari halaman publik (Glassdoor, JobStreet) — pengambilan otomatis dilarang ToS sumber, jadi dicatat manual oleh pengelola.</li>
          <li><strong>Berita:</strong> RSS berita (judul + tautan saja). Berita memberi poin hanya bila ≥ 2 media independen dan ≤ 12 bulan.</li>
          <li><strong>Media sosial:</strong> hanya sebagai lead/konteks, bukan sumber lowongan otomatis. Instagram hanya lead manual; LinkedIn bukan sumber.</li>
        </ul>
        <p className="mt-2">
          Setiap poin skor harus punya <strong>tautan bukti + tanggal bukti +
          sumber + tingkat kepercayaan</strong>. Tanpa bukti, skor tidak tampil.
          Kutipan yang ditampilkan hanya kutipan singkat, bukan salinan penuh.
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-slate-900">4. Batasan — yang tidak kami klaim</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>Skor adalah ringkasan sinyal publik, <strong>bukan penilaian hukum atau jaminan</strong>. Kami tidak pernah menulis bahwa perusahaan &ldquo;melanggar UU&rdquo; atau &ldquo;penipu&rdquo;.</li>
          <li>Satu-dua ulasan tidak pernah memberi poin. Tuduhan berat dari satu sumber tidak pernah ditulis sebagai fakta — paling jauh tampil sebagai laporan yang belum terverifikasi, beserta tautannya.</li>
          <li>Deteksi ulasan palsu diakui <strong>tidak bisa</strong> kami lakukan dengan andal — itu risiko terbuka, bukan sesuatu yang kami klaim.</li>
          <li>Sinyal kedaluwarsa: rating dihitung ulang bila data &gt; 12 bulan; keluhan &gt; 24 bulan keluar dari poin; berita &gt; 12 bulan tidak memberi poin.</li>
          <li>Tidak ada data pribadi pelamar yang disimpan atau ditampilkan (nama reviewer anonim, tanpa nama/username forum).</li>
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-slate-900">5. Cara perusahaan minta koreksi</h2>
        <p className="mt-1">
          Perusahaan yang merasa datanya salah dapat meminta koreksi dengan
          mengirim bukti yang bisa diverifikasi ke pengelola CekLoker.
          Sejak koreksi diajukan, poin sinyal yang disengketakan{" "}
          <strong>ditangguhkan</strong> (dihitung 0 sementara) dan ditampilkan
          sebagai &ldquo;disengketakan — sedang ditinjau&rdquo; sampai diputuskan,
          paling lambat <strong>7 hari</strong>. Tanggapan perusahaan yang
          sopan dan faktual diterbitkan berdampingan.
        </p>
        <p className="mt-2">
          Penghapusan hanya bila bukti salah, kedaluwarsa, atau melanggar
          aturan — bukan karena perusahaan tidak suka dengan hasilnya.
          Form koreksi online belum tersedia di versi ini; alamat kontak
          resmi akan diumumkan begitu tersedia.
        </p>
      </section>

      <section className="rounded-lg border border-slate-300 bg-white p-4">
        <h2 className="text-lg font-semibold text-slate-900">Disclaimer</h2>
        <p className="mt-1">
          Skor ini ringkasan sinyal publik, bukan penilaian hukum atau
          jaminan. Selalu cek langsung ke perusahaan sebelum memutuskan.
        </p>
      </section>

      <p>
        <Link href="/" className="text-teal-700 hover:underline">
          ← Kembali ke daftar lowongan
        </Link>
      </p>
    </div>
  );
}
