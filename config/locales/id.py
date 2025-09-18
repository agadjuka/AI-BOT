"""
Teks Indonesia untuk Telegram bot
Berisi semua teks pesan, tombol, error dan notifikasi dalam bahasa Indonesia
"""

ID_TRANSLATIONS = {
    # Pesan selamat datang
    "welcome": {
        "start_message": "Halo, {user}! 👋\n\nPilih aksi:",
        "start_instruction": "Selamat datang di bot pemindaian struk! 👋\n\nSaya akan membantu Anda secara otomatis memindahkan data dari struk langsung ke Google Sheets Anda, menghemat waktu Anda.\n\n**Untuk memulai, ikuti tiga langkah sederhana:**\n\n📊 **1. Hubungkan Google Sheets**\nIni adalah tempat di mana semua data akan disimpan. Masuk ke **Dashboard Pribadi** untuk menambahkan link ke spreadsheet Anda dan memberikan akses ke bot.\n\n📝 **2. Upload daftar bahan**\nIni adalah panduan pribadi Anda untuk produk. Ketika saya memindai «Kecap tomat Heinz Spicy» di struk, saya akan menemukan «Tomato sauce» di daftar Anda dan menuliskan nama yang tepat di spreadsheet. Dengan cara ini data Anda akan selalu bersih dan konsisten.\n\n📸 **3. Pindai struk!**\nKetika semuanya sudah dikonfigurasi, cukup kirimkan foto struk kepada saya, dan saya akan melakukan semua pekerjaan.",
        "instruction": "📖 *Instruksi Penggunaan Bot*\n\n*Fitur Utama*\n\n🔹 Pemindaian Struk - kirim foto struk dan bot akan otomatis mengekstrak semua item dan harga\n🔹 Pencocokan Bahan - bot akan menemukan item dari struk dalam daftar bahan Anda untuk penamaan yang konsisten\n🔹 Upload ke Google Sheets - semua data otomatis disimpan ke spreadsheet Anda\n\n*Cara Memulai*\n\n1️⃣ Siapkan Google Sheets di dashboard pribadi\n2️⃣ Upload daftar bahan untuk pencocokan item yang tepat\n3️⃣ Kirim foto struk untuk analisis\n\n*Fitur Tambahan*\n\n✏️ Edit - Anda dapat memperbaiki data apa pun sebelum upload\n🔄 Analisis Ulang - jika ada yang salah\n📊 Pratinjau - lihat data sebelum menyimpan\n\n*🚀 Mode TURBO*\n\n⚡ Diaktifkan - kecepatan pemrosesan foto maksimal\n⏹️ Dinonaktifkan - kualitas pemindaian maksimal\n\n*📱 Tampilan Mobile dan Desktop*\n\n📱 Smartphone - tabel kompak untuk layar kecil\n🖥️ Komputer - tabel lengkap untuk layar besar\n\n*Perintah*\n• /start - menu utama\n• /dashboard - dashboard pribadi",
        "analyze_receipt": "📸 Analisis struk\n\nKirim foto struk untuk dianalisis:",
        "main_menu": "🏠 Menu utama\n\nGunakan /start untuk memulai pekerjaan baru.",
        "choose_language": "🌍 Pilih bahasa / Choose language:",
        "new_receipt_ready": "🎉 **Siap memproses struk baru!**\n\n📸 Kirim gambar struk ke chat, dan saya akan menganalisisnya untuk Anda.\n\n✨ Bot siap bekerja!",
        "dashboard": {
            "welcome_message": "👤 Dashboard Pribadi\n\nSelamat datang, {user}!\n\nPilih pengaturan:",
            "buttons": {
                "language_settings": "🌍 Pengaturan Bahasa",
                "google_sheets_management": "⚙️ Google Sheets",
                "ingredients_management": "🥕 Daftar Bahan",
                "instruction": "📖 Instruksi",
                "turbo_mode": "🚀 TURBO",
                "turbo_mode_on": "🚀 TURBO [ON]",
                "turbo_mode_off": "🚀 TURBO [OFF]"
            }
        }
    },
    
    # Tombol antarmuka
    "buttons": {
        # Aksi utama
        "analyze_receipt": "📸 Analisis struk",
        "scan_receipt": "📸 Pindai struk",
        "personal_dashboard": "⚙️ Dashboard Pribadi",
        "back_to_receipt": "◀️ Kembali ke struk",
        "back_to_main_menu": "◀️ Kembali",
        "back": "⬅️ Kembali",
        "dashboard": "👤 Dashboard",
        
        
        # Edit struk
        "add_row": "➕ Tambah baris",
        "delete_row": "➖ Hapus baris",
        "edit_line_number": "🔢 Edit baris berdasarkan nomor",
        "edit_total": "💰 Edit Total",
        "reanalyze": "🔄 Analisis ulang",
        "upload_to_google_sheets": "📊 Upload ke Google Sheets",
        
        # Edit field
        "edit_name": "📝 Nama",
        "edit_quantity": "🔢 Jumlah", 
        "edit_price": "💰 Harga",
        "edit_total_field": "💵 Jumlah",
        "apply_changes": "✅ Terapkan",
        "cancel": "❌ Batal",
        "fix_line": "Perbaiki baris {line_number}",
        
        # Aksi dengan total
        "auto_calculate_total": "🧮 Hitung otomatis",
        "manual_edit_total": "✏️ Input manual",
        
        # Status dan aksi
        "finish": "Laporan sudah siap!",
        "noop": "Aksi tidak dikenal"
    },
    
    # Pesan error
    "errors": {
        "receipt_data_not_found": "❌ Data struk tidak ditemukan",
        "operation_cancelled": "❌ Operasi dibatalkan\n\nGunakan /start untuk memulai pekerjaan baru.",
        "unknown_action": "Aksi tidak dikenal",
        "unsupported_language": "❌ Bahasa tidak didukung",
        "language_fallback": "❌ Bahasa tidak didukung. Bahasa Rusia diatur sebagai default.",
        "field_not_specified": "❌ Error: field untuk edit tidak ditentukan.\nSilakan pilih field untuk edit dari menu.",
        "line_not_found": "Error: baris tidak ditemukan",
        "data_not_found": "Terjadi error, data tidak ditemukan.",
        "parsing_error": "Tidak dapat mengenali struktur struk. Coba buat foto lebih jelas.",
        "photo_processing_error": "Terjadi error saat memproses foto: {error}",
        "field_edit_error": "Error saat edit field: {error}",
        "total_update_error": "Error saat update total: {error}",
        "total_update_retry": "Error saat update total. Coba lagi.",
        "critical_photo_error": "❌ Error kritis saat memproses foto",
        "invalid_update_object": "Objek update tidak valid",
        "failed_to_edit_message": "Gagal edit pesan {message_id}: {error}",
        "failed_to_delete_message": "Gagal hapus pesan {message_id}: {error}",
        "failed_to_delete_temporary_message": "Gagal hapus pesan sementara {message_id}: {error}",
        "photos_already_processing": "❌ Foto sedang diproses. Silakan tunggu selesai.",
        "too_many_photos": "❌ Terlalu banyak foto. Maksimal {max_photos} foto sekaligus.",
        "multiple_photos_error": "❌ Error saat memproses beberapa foto: {error}",
        "no_successful_photos": "❌ Tidak ada foto yang berhasil diproses. Coba lagi dengan foto yang lebih jelas.",
        "no_photos_in_group": "❌ Tidak ada foto ditemukan dalam grup media."
    },
    
    # Pesan validasi
    "validation": {
        "line_number_too_small": "Nomor baris harus lebih dari 0",
        "line_number_too_large": "Nomor baris {line_number} melebihi maksimal {max_line_number}",
        "line_not_found": "Baris {line_number} tidak ditemukan",
        "field_negative": "{field_name} tidak bisa negatif",
        "invalid_line_format": "Format tidak valid. Masukkan hanya nomor baris (contoh: `3`):",
        "negative_value": "Nilai tidak bisa negatif. Coba lagi.",
        "negative_total": "Total tidak bisa negatif. Coba lagi.",
        "try_again": "Coba lagi:",
        "no_items": "Tidak ada item produk",
        "incorrect_line_numbering": "Penomoran baris salah: {line_numbers}, diharapkan: {expected_numbers}",
        "missing_name_field": "Field name hilang di baris {line_number}",
        "missing_status_field": "Field status hilang di baris {line_number}",
        "missing_quantity_field": "Field quantity hilang di baris {line_number}",
        "missing_price_field": "Field price hilang di baris {line_number}",
        "missing_total_field": "Field total hilang di baris {line_number}",
        "calculation_warning": "Peringatan: Baris {line_number} - perhitungan tidak cocok: {quantity} * {price} = {expected_total}, tapi struk menunjukkan {total}",
        "data_correct": "Data benar",
        "line_number_correct": "Nomor baris benar",
        "field_cannot_be_empty": "{field_name} tidak bisa kosong",
        "invalid_numeric_format": "Format {field_name} tidak valid. Masukkan angka",
        "value_correct": "Nilai benar",
        "field_too_long": "{field_name} terlalu panjang (maksimal 100 karakter)"
    },
    
    # Pesan status
    "status": {
        "processing_receipt": "🔄 Memproses struk",
        "analyzing_receipt": "🔄 Menganalisis foto ulang...",
        "processing": "Memproses...",
        "total_auto_calculated": "✅ Total dihitung otomatis: **{total}**",
        "line_deleted": "✅ Baris {line_number} dihapus! Memperbarui tabel...",
        "total_updated": "✅ Total diperbarui: **{total}**",
        "analysis_started": "🔍 Memulai analisis struk...",
        "analysis_completed": "✅ Analisis selesai",
        "ingredients_loaded": "✅ Dimuat {count} bahan dari Google Sheets",
        "processing_multiple_photos": "📸 Memproses {total} foto... ({processed}/{total})",
        "processing_multiple_photos_progress": "📸 Memproses foto...\n\n✅ Berhasil: {successful}\n❌ Gagal: {failed}\n📊 Progress: {processed}/{total}",
        "multiple_photos_completed": "✅ Pemrosesan beberapa foto selesai!\n\n📊 Hasil:\n• Total foto: {total}\n• Berhasil: {successful}\n• Gagal: {failed}"
    },
    
    # Pesan analisis
    "analysis": {
        "errors_found": "🔴 **Ditemukan error dalam data struk**\n\n",
        "total_matches": "✅ **Total sesuai!**\n",
        "total_mismatch": "❗ **Total tidak sesuai! Selisih: {difference}**\n",
        "auto_calculated": "*(dihitung otomatis)*",
        "editing_line": "**Edit baris {line_number}:** {status_icon}\n\n",
        "editing_total": "**Edit total:**\n\n",
        "current_total": "💰 **Total saat ini:** {total}\n",
        "calculated_total": "🧮 **Total dihitung otomatis:** {calculated_total}\n\n",
        "choose_action": "Pilih aksi:",
        "choose_field": "Pilih field untuk edit:",
        "field_name": "📝 **Nama:** {name}\n",
        "field_quantity": "🔢 **Jumlah:** {quantity}\n", 
        "field_price": "💰 **Harga:** {price}\n",
        "field_total": "💵 **Jumlah:** {total}\n\n",
        "deleting_line": "🗑️ Hapus baris\n\nMasukkan nomor baris untuk dihapus:",
        "editing_line_input": "✏️ Edit baris\n\nMasukkan nomor baris untuk diedit:",
        "editing_total_input": "💰 Edit total\n\nMasukkan total baru:",
        "field_display_names": {
            "name": "nama barang",
            "quantity": "jumlah", 
            "price": "harga",
            "total": "jumlah"
        },
        "field_edit_input": "✏️ Edit {field_name} untuk baris {line_number}\n\nMasukkan nilai baru:",
        "new_item_name": "Barang baru",
        "deleting_item_confirmation": "🗑️ Hapus item {item_number}\n\nKonfirmasi penghapusan (ya/tidak):"
    },
    
    # Pesan pencocokan bahan
    "matching": {
        "no_ingredients": "Tidak ada bahan untuk dicocokkan.",
        "matching_title": "**Pencocokan bahan:**\n",
        "statistics": "📊 **Statistik:** Total: {total} | 🟢 Tepat: {exact} | 🟡 Sebagian: {partial} | 🔴 Tidak ditemukan: {none}\n",
        "table_header": "{'№':<2} | {'Barang':<{name_width}} | {'Google Sheets':<{name_width}} | {'Status':<4}",
        "manual_instructions": "**Instruksi pencocokan manual:**\n\n1. Pilih nomor saran untuk pencocokan otomatis\n2. Atau masukkan '0' untuk melewatkan bahan ini\n3. Atau masukkan 'search: <nama>' untuk mencari opsi lain\n\nContoh:\n• `1` - pilih saran pertama\n• `0` - lewati\n• `search: tomat` - cari opsi dengan 'tomat'",
        "no_search_results": "Tidak ditemukan hasil untuk '{query}'.",
        "search_results": "**Hasil pencarian untuk '{query}':**\n",
        
        # Pesan pemrosesan input
        "matching_data_not_found": "Error: data pencocokan tidak ditemukan.",
        "failed_to_delete_message": "Gagal menghapus pesan pengguna: {error}",
        "enter_search_query": "Masukkan query pencarian setelah 'search:'",
        "ingredient_skipped": "✅ Bahan dilewati: {ingredient_name}",
        "ingredient_matched": "✅ Dicocokkan: {receipt_item} → {matched_ingredient}",
        "invalid_suggestion_number": "Nomor tidak valid. Masukkan nomor dari 1 sampai {max_number} atau 0 untuk melewatkan.",
        "invalid_format": "Format tidak valid. Masukkan nomor saran, 0 untuk melewatkan atau 'search: query' untuk mencari.",
        "processing_error": "Error memproses pencocokan manual: {error}",
        "try_again": "Terjadi error. Coba lagi.",
        
        # Pesan pencarian
        "search_results_title": "**Hasil pencarian untuk '{query}':**\n\n",
        "found_variants": "Ditemukan varian: **{count}**\n\n",
        "select_ingredient": "**Pilih bahan untuk dicocokkan:**\n",
        "no_suitable_variants": "❌ **Tidak ditemukan varian yang sesuai untuk '{query}'**\n\nCoba query pencarian lain atau kembali ke ringkasan.",
        "nothing_found": "❌ **Tidak ditemukan hasil untuk '{query}'**\n\nCoba query pencarian lain atau kembali ke ringkasan.",
        "no_suitable_results": "Tidak ditemukan varian yang sesuai untuk '{query}' (dengan probabilitas > 50%).",
        "search_nothing_found": "Tidak ditemukan hasil untuk '{query}'.",
        
        # Tombol pencarian
        "new_search": "🔍 Pencarian baru",
        "back_to_receipt": "📋 Kembali ke ringkasan",
        "skip_ingredient": "⏭️ Lewati",
        "back": "◀️ Kembali",
        
        # Pesan pencocokan posisi
        "invalid_line_number": "Nomor baris tidak valid. Masukkan nomor dari 1 sampai {max_lines}",
        "line_selected": "Baris {line_number} dipilih. Sekarang masukkan nama bahan dari Google Sheets untuk pencarian:",
        "invalid_line_format": "Format tidak valid. Masukkan hanya nomor baris (contoh: `3`):",
        
        # Progress pencocokan
        "matching_progress": "**Pencocokan bahan** ({current}/{total})\n\n",
        "current_item": "**Barang saat ini:** {item_name}\n\n",
        "auto_matched": "✅ **Otomatis dicocokkan:** {ingredient_name}\n\n",
        "continue_instruction": "Tekan /continue untuk ke barang berikutnya.",
        
        # Hasil akhir
        "rematch_ingredients": "🔄 Cocokkan ulang bahan",
        "back_to_receipt_final": "📋 Kembali ke struk",
        
        # Pesan callback untuk pencocokan bahan
        "callback": {
            "results_not_found": "❌ Hasil pencocokan tidak ditemukan",
            "manual_matching": "✏️ Pencocokan manual",
            "show_table": "📊 Tampilkan tabel",
            "back_to_edit": "◀️ Kembali",
            "auto_match_all": "🔄 Pencocokan otomatis",
            "matching_overview_title": "🔍 **Ringkasan pencocokan bahan**\n\n",
            "statistics_title": "📊 **Statistik:**\n",
            "matched_count": "✅ Dicocokkan: {count}\n",
            "partial_count": "⚠️ Sebagian: {count}\n",
            "no_match_count": "❌ Tidak dicocokkan: {count}\n",
            "total_positions": "📝 Total posisi: {count}\n\n",
            "choose_action": "Pilih aksi:",
            "position_selection_title": "🔍 **Pilih posisi untuk dicocokkan:**\n\n",
            "invalid_position_index": "❌ Indeks posisi tidak valid",
            "invalid_suggestion_number": "❌ Nomor saran tidak valid",
            "matching_position_title": "🔍 **Pencocokan posisi {position}:**\n\n",
            "receipt_item": "📝 **Barang struk:** {item_name}\n\n",
            "suggestions_title": "💡 **Saran:**\n",
            "no_suggestions": "❌ Tidak ada saran ditemukan\n",
            "manual_search": "🔍 Pencarian manual",
            "skip_item": "❌ Lewati",
            "back_to_list": "◀️ Kembali ke daftar",
            "matching_completed": "✅ **Pencocokan selesai!**\n\n",
            "matched_item": "📝 **Barang:** {item_name}\n",
            "matched_ingredient": "🎯 **Bahan:** {ingredient_name}\n",
            "similarity_score": "📊 **Kesamaan:** {score:.2f}\n\n",
            "continue_to_next": "Pindah ke posisi berikutnya...",
            "next_position": "➡️ Posisi berikutnya",
            "matching_finished": "🎉 **Pencocokan selesai!**\n\n",
            "results_title": "📊 **Hasil:**\n",
            "matched_percentage": "📈 Persentase: {percentage:.1f}%\n\n",
            "all_matched": "🎯 Semua posisi berhasil dicocokkan!",
            "remaining_items": "⚠️ Masih perlu dicocokkan: {count} posisi",
            "back_to_editing": "◀️ Kembali ke edit",
            "changes_applied": "✅ Perubahan pencocokan diterapkan!\n\nPindah ke langkah berikutnya...",
            "search_ingredient": "🔍 Cari bahan\n\nMasukkan nama bahan untuk pencarian:",
            "back_without_changes": "✅ Kembali tanpa menyimpan perubahan\n\nPerubahan tidak disimpan.",
            "cancel_back": "❌ Batalkan kembali\n\nMelanjutkan dengan data saat ini."
        }
    },
    
    # Pesan manajemen Google Sheets
    "sheets_management": {
        "title": "📊 Manajemen Google Sheets",
        "no_sheets_description": "Anda belum memiliki sheet yang terhubung. Mari tambahkan yang pertama!",
        "has_sheets_description": "Berikut adalah sheet yang terhubung. Sheet dengan bintang (⭐) digunakan secara default untuk upload struk.",
        "add_new_sheet_instruction": "📊 **Tambah Google Sheet Baru**\n\nFitur ini akan segera hadir! Di sini Anda akan dapat menambah dan mengkonfigurasi Google Sheets Anda.",
        "buttons": {
            "add_new_sheet": "➕ Tambah sheet baru",
            "back_to_dashboard": "⬅️ Kembali"
        }
    },
    
    # Pesan manajemen bahan
    "ingredients": {
        "management": {
            "no_ingredients": "🥕 Manajemen Daftar Bahan\n\nAnda belum memiliki daftar bahan pribadi. Daftar ini digunakan untuk pengenalan yang lebih akurat dari item dalam struk.\n\nAnda dapat mengunggah daftar Anda sebagai file teks sederhana (.txt) atau mengirimkannya sebagai pesan teks di mana setiap bahan ditulis dalam baris baru.",
            "has_ingredients": "🥕 Manajemen Daftar Bahan\n\nAnda memiliki daftar pribadi yang dimuat. Ini digunakan untuk mencocokkan item dalam struk.",
            "list_display": "🥕 Daftar Bahan Anda\n\n{ingredients}\n\nPilih aksi:",
            "replace_instruction": "🔄 Ganti Daftar Bahan\n\nKirim file teks baru (.txt) dengan bahan di mana setiap bahan ditulis dalam baris baru.\n\nFile ini akan mengganti daftar Anda saat ini.",
            "file_upload_instruction": "📥 Unggah File Bahan\n\nKirim file teks (.txt) dengan bahan di mana setiap bahan ditulis dalam baris baru.\n\nContoh isi file:\nSusu\nRoti\nTelur\nMentega",
            "file_upload_request": "Silakan kirim file teks (.txt) dengan daftar bahan Anda. Setiap bahan harus dalam baris terpisah.",
            "text_upload_request": "📝 Unggah Daftar dari Teks\n\nKirim daftar bahan Anda sebagai pesan teks di mana setiap bahan ditulis dalam baris baru.\n\nContoh:\nSusu\nRoti\nTelur\nMentega",
            "text_upload_success": "✅ Daftar {count} bahan berhasil dimuat dari teks!",
            "text_upload_error_empty": "Pesan kosong atau tidak berisi bahan yang valid.",
            "text_upload_error_processing": "Error memproses teks. Silakan coba lagi.",
            "file_upload_success": "✅ Daftar {count} bahan berhasil dimuat!",
            "file_upload_error_format": "Silakan kirim file dalam format .txt.",
            "file_upload_error_empty": "File kosong atau tidak berisi bahan yang valid.",
            "file_upload_error_processing": "Error memproses file. Silakan coba lagi.",
            "delete_confirmation": "🗑️ Hapus Daftar Bahan\n\nApakah Anda yakin ingin menghapus daftar bahan pribadi Anda?\n\nTindakan ini tidak dapat dibatalkan.",
            "delete_success": "✅ Daftar Bahan Dihapus\n\nDaftar bahan pribadi Anda telah berhasil dihapus.",
            "delete_error": "❌ Error Penghapusan\n\nGagal menghapus daftar bahan. Silakan coba lagi.",
            "buttons": {
                "upload_file": "📥 Unggah File",
                "upload_text": "📝 Unggah dari Teks",
                "view_list": "📄 Lihat Daftar",
                "replace_list": "🔄 Ganti Daftar",
                "delete_list": "🗑️ Hapus Daftar",
                "confirm_delete": "✅ Ya, Hapus",
                "cancel_delete": "❌ Batal"
            }
        }
    },
    
    # Pesan tambah sheet baru
    "add_sheet": {
        "step1_title": "📄 Menambah Tabel (Langkah 1 dari 2)",
        "step1_instruction": "Untuk menghubungkan tabel, ikuti langkah-langkah berikut:\n\n📝 1. Buat Google Sheet baru, atau gunakan yang sudah ada (pastikan tidak ada informasi rahasia).\n\n🔗 2. Klik tombol 'Bagikan' di pojok kanan atas di Google Sheets.\n\n📧 3. Di field 'Tambahkan orang dan grup', tempel email ini:\n\n<code>{service_email}</code>\n\n✅ 4. Pastikan Anda memberikan izin <b>Editor</b>.\n\n📋 5. Salin link sheet dari browser dan kirim ke saya dalam pesan berikutnya.",
        "step2_title": "📝 Pilih Nama (Langkah 2 dari 3)",
        "step2_instruction": "✅ Bagus, akses diberikan! Sekarang pilih nama sederhana untuk tabel agar tidak bingung. Contoh: <i>Pengeluaran Rumah</i>.",
        "step3_title": "📊 Konfigurasi Tabel (Langkah 3 dari 3)",
        "step3_instruction": "Sempurna! Tabel terhubung. Secara default, data akan ditulis sebagai berikut:",
        "step3_sheet_info": "Data akan ditulis ke sheet: <code>Sheet1</code>",
        "step3_question": "Gunakan pengaturan ini atau konfigurasi sendiri?",
        "table_headers": {
            "date": "Tanggal",
            "product": "Barang", 
            "quantity": "Jml",
            "price": "Harga",
            "sum": "Jumlah",
            "name": "Nama",
            "ingredient": "Bahan"
        },
        "step3_success": "🎉 Tabel '{sheet_name}' berhasil ditambahkan!",
        "buttons": {
            "cancel": "⬅️ Batal",
            "use_default": "✅ Gunakan default",
            "configure_manual": "✏️ Konfigurasi manual"
        },
        "mapping_editor": {
            "title": "⚙️ Editor Pengaturan Tabel",
            "description": "Konfigurasi pemetaan antara field struk dan kolom tabel:",
            "sheet_info": "Sheet: <code>{sheet_name}</code>",
            "current_settings": "**Pengaturan saat ini:**",
            "field_mapping": "{field_name} ➡️ Kolom {column}",
            "field_buttons": {
                "check_date": "🗓️ Tanggal Saat Ini",
                "product_name": "📦 Nama Barang", 
                "quantity": "🔢 Jumlah",
                "price_per_item": "💰 Harga per Item",
                "total_price": "💵 Total Harga"
            },
            "action_buttons": {
                "save_and_exit": "✅ Simpan dan Keluar",
                "cancel": "⬅️ Batal",
                "sheet": "📄 Sheet",
            },
            "column_input": "Tentukan kolom baru untuk field '{field_name}' (contoh: `C`) atau tulis `-` untuk tidak menggunakan field ini.",
            "field_names": {
                "check_date": "Tanggal Saat Ini",
                "product_name": "Nama Barang",
                "quantity": "Jumlah", 
                "price_per_item": "Harga per Item",
                "total_price": "Total Harga"
            },
            "sheet_name_input": "Tentukan **nama sheet baru** (contoh: `Sales Data`). Nama harus persis sama dengan nama sheet di Google Spreadsheet Anda."
        },
        "errors": {
            "invalid_url": "🤔 Tidak dapat mengakses tabel. Silakan periksa kembali bahwa Anda memberikan izin <b>Editor</b> khusus untuk email ini. Coba kirim link lagi.",
            "invalid_sheet_id": "❌ Tidak dapat mengekstrak ID tabel dari link. Silakan kirim link Google Sheet yang benar.",
            "save_failed": "⚠️ Error menyimpan tabel. Coba lagi.",
            "jwt_error": "⚠️ Masalah pemeriksaan akses. Melanjutkan proses penambahan tabel.",
            "invalid_column": "❌ Format kolom tidak valid. Masukkan huruf (A-Z) atau `-` untuk menonaktifkan.",
            "invalid_row_number": "❌ Nomor baris tidak valid. Masukkan angka positif (contoh: `2`).",
            "no_field_selected": "❌ Tidak ada field yang dipilih untuk diedit."
        }
    },
    
    # Pesan Google Sheets
    "sheets": {
        "ingredients_loaded": "✅ Dimuat {count} bahan Google Sheets sesuai permintaan",
        "no_data_for_upload": "❌ **Tidak ada data untuk diupload**\n\nPertama perlu upload dan analisis struk.\nKlik 'Analisis struk' dan upload foto struk.",
        "no_personal_ingredients": "❌ **Tidak ada bahan pribadi**\n\nAnda belum memuat daftar bahan untuk pencocokan.\nSilakan upload daftar bahan Anda di pengaturan terlebih dahulu.",
        
        # Pesan pencarian Google Sheets
        "no_line_selected": "Error: tidak ada baris yang dipilih untuk pencocokan.",
        "dictionary_not_loaded": "Error: kamus Google Sheets tidak dimuat.",
        "no_search_results": "Tidak ditemukan hasil untuk '{query}' di Google Sheets.",
        "no_item_selected": "Error: tidak ada item yang dipilih untuk pencarian.",
        "ingredients_loaded_for_search": "✅ Dimuat {count} bahan Google Sheets untuk pencarian",
        "using_cached_ingredients": "✅ Menggunakan {count} bahan Google Sheets yang sudah dimuat",
        "search_results_title": "**Hasil pencarian Google Sheets untuk '{query}':**\n\n",
        "back_button": "◀️ Kembali",
        
        # Pesan callback untuk Google Sheets
        "callback": {
            "matching_results_not_found": "❌ Hasil pencocokan tidak ditemukan",
            "choose_action_for_matching": "Pilih aksi untuk bekerja dengan pencocokan:",
            "preview_data_not_found": "❌ Data untuk preview tidak ditemukan",
            "upload_preview_title": "📊 **Preview upload ke Google Sheets**",
            "uploading_data": "📤 Mengupload data ke Google Sheets...",
            "receipt_data_not_found": "Data struk tidak ditemukan",
            "upload_successful": "Upload berhasil",
            "upload_error": "❌ Error upload: {message}",
            "no_sheet_configured": "❌ Google Sheet belum dikonfigurasi\n\nSilakan konfigurasi Google Sheet di pengaturan bot terlebih dahulu.",
            "service_not_available": "❌ Layanan Google Sheets tidak tersedia\n\nPeriksa pengaturan koneksi.",
            "quota_exceeded": "⚠️ Kuota API Google Sheets terlampaui\n\nSilakan coba upload data nanti. Sistem akan otomatis mencoba lagi.",
            "permission_denied": "❌ Tidak ada akses ke Google Sheet\n\nPeriksa izin service account.",
            "sheet_not_found": "❌ Google Sheet tidak ditemukan\n\nPeriksa URL sheet sudah benar.",
            "matching_data_not_found": "Error: data pencocokan tidak ditemukan.",
            "dictionary_not_loaded": "Gagal memuat kamus bahan Google Sheets.\nPeriksa pengaturan konfigurasi.",
            "all_positions_processed": "✅ Semua posisi diproses!",
            "choose_position_for_matching": "**Pilih posisi untuk pencocokan**",
            "matching_updated": "✅ Pencocokan diperbarui!",
            "data_successfully_uploaded": "✅ **Data berhasil diupload ke Google Sheets!**",
            "no_upload_data_for_undo": "Tidak ada data tentang upload terakhir untuk dibatalkan",
            "no_data_to_undo": "Tidak ada data untuk dibatalkan",
            "undo_upload_failed": "Gagal membatalkan upload: {message}",
            "unexpected_error": "❌ **Error kritis**\n\nTerjadi error tak terduga saat mengupload ke Google Sheets:\n`{error}`",
            "no_receipt_data_for_file": "❌ Tidak ada data struk untuk pembuatan file.",
            "no_matching_data_for_file": "❌ Tidak ada data pencocokan Google Sheets untuk pembuatan file.",
            "excel_generation_error": "❌ Error membuat file Excel.",
            "excel_generation_error_detailed": "❌ Error membuat file Excel: {error}",
            "matching_table_title": "**Pencocokan dengan Google Sheets:**",
            "no_ingredients_for_matching": "Tidak ada bahan untuk dicocokkan.",
            "table_header": "№ | Nama                         | Bahan                        | Status",
            "manual_matching_editor_title": "**Editor pencocokan Google Sheets**",
            "current_item": "**Barang:** {item_name}",
            "choose_suitable_ingredient": "**Pilih bahan yang sesuai:**",
            "no_suitable_options": "❌ **Tidak ada opsi yang sesuai ditemukan**",
            "undo_error_title": "❌ **{error_message}**",
            "undo_error_info": "Informasi tentang upload terakhir tidak ditemukan.",
            "undo_successful": "✍️ **Upload berhasil dibatalkan!**",
            "cancelled_rows": "📊 **Baris yang dibatalkan:** {row_count}",
            "worksheet_name": "📋 **Lembar kerja:** {worksheet_name}",
            "undo_time": "🕒 **Waktu pembatalan:** {time}",
            "data_deleted_from_sheets": "Data telah dihapus dari Google Sheets.",
            "no_data_for_preview": "❌ **Tidak ada data untuk pratinjau**\n\nTidak dapat menemukan data struk untuk menampilkan pratinjau Google Sheets.",
            "excel_file_created": "📄 **File Excel dengan data struk dibuat!**",
            "excel_success_title": "✅ **File Excel berhasil dibuat!**",
            "excel_success_description": "File berisi data yang sama yang diupload ke Google Sheets.",
            "file_available_for_download": "⏰ **File akan tersedia untuk download selama 5 menit**",
            "no_data_to_display": "Tidak ada data untuk ditampilkan",
            "no_sheets_found": "❌ Anda tidak memiliki lembar yang terhubung",
            "no_sheet_selected": "❌ Tidak ada lembar yang dipilih",
            "sheet_not_found": "❌ Lembar tidak ditemukan",
            "switching_sheet": "🔄 Beralih lembar...",
            "date_header": "Tanggal",
            "volume_header": "Vol",
            "price_header": "harga",
            "product_header": "Produk",
            "total_label": "Total:",
            "new_item_name": "Barang baru",
            "invalid_item_index": "Error: indeks item tidak valid.",
            "invalid_suggestion_index": "Error: indeks saran tidak valid.",
            "invalid_search_result_index": "Error: indeks hasil pencarian tidak valid.",
            "matched_successfully": "✅ Dicocokkan: {receipt_item} → {ingredient_name}",
            "edit_matching": "✏️ Edit pencocokan",
            "preview": "👁️ Preview",
            "back_to_receipt": "◀️ Kembali ke struk",
            "upload_to_google_sheets": "✅ Upload ke Google Sheets",
            "upload_to_sheet": "📊 Upload ke '{sheet_name}'",
            "upload_to_main_sheet": "✅ Upload ke '{sheet_name}'",
            "back": "◀️ Kembali",
            "select_position_for_matching": "🔍 Pilih posisi untuk pencocokan",
            "search": "🔍 Cari",
            "undo_upload": "↩️ Batalkan upload",
            "generate_file": "📄 Buat file",
            "upload_new_receipt": "📸 Upload struk baru",
            "back_to_receipt_button": "📋 Kembali ke struk",
            "preview_google_sheets": "👁️ Preview Google Sheets",
            "no_default_sheet_found": "❌ Sheet default pengguna tidak ditemukan",
            "no_column_mapping_found": "❌ Mapping kolom tidak ditemukan untuk sheet default",
            "sheet_name_label": "**Lembar:** `{sheet_name}`"
        }
    },
    
    # Pesan file
    "files": {
        "no_data": "Tidak ada data untuk ditampilkan",
        "table_header": "{'№':^{number_width}} | {'Barang':<{product_width}} | {'Jml':^{quantity_width}} | {'Harga':^{price_width}} | {'Jumlah':>{total_width}} | {'':^{status_width}}",
        "total_label": "Total:"
    },
    
    # Pesan pembuatan file
    "file_generation": {
        "generating_file": "📄 Membuat file...",
        "file_ready": "📄 File untuk upload {file_type} siap!",
        "success_title": "✅ **File {file_type} berhasil dibuat!**",
        "filename": "📁 **Nama file:** {filename}",
        "positions_count": "📊 **Posisi:** {count}",
        "generation_date": "📅 **Tanggal:** {date}",
        "show_table": "📊 Tampilkan tabel",
        "back_to_edit": "◀️ Kembali ke edit",
        "download_google_sheets_file": "📊 Download file Google Sheets",
        "matching_table_title": "📊 **Tabel pencocokan bahan:**",
        "table_header": "| № | Item struk | Bahan | Status | Kesamaan |",
        "table_separator": "|---|---|---|---|---|",
        "legend_title": "💡 **Legenda:**",
        "legend_matched": "✅ - Dicocokkan",
        "legend_partial": "⚠️ - Sebagian dicocokkan",
        "legend_not_matched": "❌ - Tidak dicocokkan",
        "not_matched": "Tidak dicocokkan",
        "error_generating_file": "❌ Error membuat file: {error}",
        "google_sheets_handler_unavailable": "❌ Google Sheets handler tidak tersedia untuk pembuatan Excel",
        "ingredient_matching_handler_unavailable": "❌ Ingredient matching handler tidak tersedia",
        "matching_results_not_found": "❌ Hasil pencocokan tidak ditemukan",
        "receipt_data_not_found": "❌ Data struk tidak ditemukan"
    },
    
    # Pesan umum dan helper
    "common": {
        "no_data_to_display": "Tidak ada data untuk ditampilkan",
        "page": "Halaman {page}",
        "unknown_ingredient_type": "DEBUG: Tipe bahan tidak dikenal: {ingredient_type}",
        "loaded_google_sheets_ingredients": "✅ Dimuat {count} bahan Google Sheets sesuai permintaan",
        "debug_first_ingredients": "DEBUG: 5 bahan pertama: {ingredients}",
        "navigation_buttons": {
            "first_page": "⏮️",
            "previous_page": "◀️", 
            "next_page": "▶️",
            "last_page": "⏭️"
        },
        "status_emojis": {
            "confirmed": "✅",
            "error": "🔴",
            "partial": "⚠️",
            "no_match": "❌",
            "exact_match": "🟢",
            "matched": "✅",
            "partial_match": "🟡",
            "unknown": "❓"
        }
    },
    
    # Pesan pemformatan
    "formatters": {
        "no_data_to_display": "Tidak ada data untuk ditampilkan",
        "table_headers": {
            "number": "№",
            "product": "Barang",
            "quantity": "Jml",
            "price": "Harga",
            "amount": "Jumlah",
            "name": "Nama",
            "ingredient": "Bahan"
        },
        "total_label": "Total:"
    },
    
    # Kontrol akses
    "access_control": {
        "access_denied": "Maaf, Anda tidak memiliki akses ke bot ini. Silakan hubungi administrator @markov1u",
        "admin_only": "Perintah ini hanya tersedia untuk administrator."
    },
    
    # Mode TURBO
    "turbo_mode": {
        "enabled_simple": "🚀 Mode TURBO diaktifkan\n\n_Pemrosesan file dengan kecepatan maksimal\\._\n_Kualitas pemindaian mungkin berkurang\\._\n_Tidak disarankan untuk kuitansi tulisan tangan\\._",
        "disabled_simple": "⏹️ Mode TURBO dinonaktifkan\n\n_Kualitas pemindaian kuitansi maksimal\\._",
        "enabled": "🚀 Mode TURBO diaktifkan\n\nSekarang semua pemrosesan foto akan dikirim langsung ke Gemini Flash tanpa pemrosesan OpenCV untuk kecepatan maksimal!\n\n🔍 **Analisis OpenCV dinonaktifkan**",
        "disabled": "🚀 Mode TURBO dinonaktifkan\n\nKembali ke pemrosesan standar menggunakan OpenCV.\n\n🔍 **Analisis OpenCV diaktifkan**",
        "status_enabled": "✅ Mode TURBO diaktifkan (OpenCV dinonaktifkan)",
        "status_disabled": "❌ Mode TURBO dinonaktifkan (OpenCV diaktifkan)",
        "description": "🚀 **Mode TURBO**\n\nDalam mode ini, foto dikirim langsung ke Gemini Flash tanpa pemrosesan awal OpenCV.\n\n**Keuntungan:**\n• ⚡ Kecepatan pemrosesan maksimal\n• 🎯 Kerja AI langsung\n\n**Kerugian:**\n• 📷 Optimasi gambar lebih sedikit\n• 🔍 Mungkin kurang akurat untuk foto buruk\n\n**Ketergantungan terbalik:**\n• TURBO aktif → OpenCV nonaktif\n• TURBO nonaktif → OpenCV aktif\n\n**Status saat ini:** {status}",
        "buttons": {
            "toggle_turbo": "🚀 Toggle TURBO",
            "back_to_dashboard": "⬅️ Kembali ke dashboard"
        }
    },
    
    # Notifikasi toggle mode tampilan
    "display_mode_notifications": {
        "mobile_selected": "📱 Antarmuka ponsel dipilih",
        "desktop_selected": "🖥️ Antarmuka desktop dipilih",
        "error_switching": "❌ Error saat mengganti mode tampilan"
    },
    
    # Tombol perangkat
    "device_buttons": {
        "smartphone": "📱 Smartphone ✔️",
        "computer": "🖥️ Komputer ✔️"
    }
    
}