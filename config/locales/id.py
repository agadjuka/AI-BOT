"""
Teks Indonesia untuk Telegram bot
Berisi semua teks pesan, tombol, error dan notifikasi dalam bahasa Indonesia
"""

ID_TRANSLATIONS = {
    # Pesan selamat datang
    "welcome": {
        "start_message": "Halo, {user}! 👋\n\nPilih aksi:",
        "analyze_receipt": "📸 Analisis struk\n\nKirim foto struk untuk dianalisis:",
        "main_menu": "🏠 Menu utama\n\nGunakan /start untuk memulai pekerjaan baru."
    },
    
    # Tombol antarmuka
    "buttons": {
        # Aksi utama
        "analyze_receipt": "📸 Analisis struk",
        "generate_supply_file": "📄 Dapatkan file untuk upload ke poster",
        "back_to_receipt": "◀️ Kembali ke struk",
        "back_to_main_menu": "◀️ Kembali",
        
        
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
        "critical_photo_error": "❌ Error kritis saat memproses foto: {error}"
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
        "try_again": "Coba lagi:"
    },
    
    # Pesan status
    "status": {
        "processing_receipt": "Memproses struk",
        "analyzing_receipt": "🔄 Menganalisis foto ulang...",
        "processing": "Memproses...",
        "total_auto_calculated": "✅ Total dihitung otomatis: **{total}**",
        "line_deleted": "✅ Baris {line_number} dihapus! Memperbarui tabel...",
        "total_updated": "✅ Total diperbarui: **{total}**",
        "analysis_started": "🔍 Memulai analisis struk...",
        "analysis_completed": "✅ Analisis selesai",
        "ingredients_loaded": "✅ Dimuat {count} bahan dari Google Sheets"
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
        "new_item_name": "Barang baru"
    },
    
    # Pesan pencocokan bahan
    "matching": {
        "no_ingredients": "Tidak ada bahan untuk dicocokkan.",
        "matching_title": "**Pencocokan bahan:**\n",
        "statistics": "📊 **Statistik:** Total: {total} | 🟢 Tepat: {exact} | 🟡 Sebagian: {partial} | 🔴 Tidak ditemukan: {none}\n",
        "table_header": "{'№':<2} | {'Barang':<{name_width}} | {'Poster':<{name_width}} | {'Status':<4}",
        "manual_instructions": "**Instruksi pencocokan manual:**\n\n1. Pilih nomor saran untuk pencocokan otomatis\n2. Atau masukkan '0' untuk melewatkan bahan ini\n3. Atau masukkan 'search: <nama>' untuk mencari opsi lain\n\nContoh:\n• `1` - pilih saran pertama\n• `0` - lewati\n• `search: tomat` - cari opsi dengan 'tomat'",
        "no_search_results": "Tidak ditemukan hasil untuk '{query}'.",
        "search_results": "**Hasil pencarian untuk '{query}':**\n"
    },
    
    # Pesan Google Sheets
    "sheets": {
        "ingredients_loaded": "✅ Dimuat {count} bahan Google Sheets sesuai permintaan",
        "no_data_for_upload": "❌ **Tidak ada data untuk diupload**\n\nPertama perlu upload dan analisis struk.\nKlik 'Analisis struk' dan upload foto struk."
    },
    
    # Pesan file
    "files": {
        "no_data": "Tidak ada data untuk ditampilkan",
        "table_header": "{'№':^{number_width}} | {'Barang':<{product_width}} | {'Jml':^{quantity_width}} | {'Harga':^{price_width}} | {'Jumlah':>{total_width}} | {'':^{status_width}}",
        "total_label": "Total:"
    },
    
    # Pesan debug
    "debug": {
        "no_matching_result": "DEBUG: Tidak ditemukan hasil pencocokan untuk update setelah {change_type}",
        "item_edited": "DEBUG: Item diedit - pencocokan bahan mungkin perlu diulang",
        "matching_updated": "DEBUG: Pencocokan bahan diperbarui setelah {change_type}, hash baru: {new_receipt_hash}, sukses: {success}",
        "matching_update_error": "DEBUG: Error update pencocokan bahan setelah {change_type}: {error}",
        "no_matching_result_deletion": "DEBUG: Tidak ditemukan hasil pencocokan untuk update setelah penghapusan",
        "matching_updated_deletion": "DEBUG: Pencocokan bahan diperbarui setelah penghapusan, hash baru: {new_receipt_hash}, sukses: {success}",
        "deleted_line_not_found": "DEBUG: Tidak dapat menemukan indeks pencocokan untuk baris yang dihapus {deleted_line_number}",
        "deletion_error": "DEBUG: Error update pencocokan bahan setelah penghapusan: {error}"
    }
}