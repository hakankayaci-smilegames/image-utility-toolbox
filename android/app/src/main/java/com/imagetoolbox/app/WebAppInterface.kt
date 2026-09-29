package com.imagetoolbox.app

import android.content.ClipData
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.provider.MediaStore
import android.util.Base64
import android.webkit.JavascriptInterface
import android.widget.Toast
import androidx.core.content.FileProvider
import java.io.File
import java.io.FileOutputStream
import java.io.OutputStream

class WebAppInterface(private val activity: MainActivity) {

    private val mainHandler = Handler(Looper.getMainLooper())

    @JavascriptInterface
    fun openPhotoPicker() {
        mainHandler.post {
            activity.launchPhotoPicker()
        }
    }

    @JavascriptInterface
    fun openMultiPhotoPicker() {
        mainHandler.post {
            activity.launchMultiPhotoPicker()
        }
    }

    @JavascriptInterface
    fun saveImageToGallery(base64Data: String, fileName: String, mimeType: String): String {
        try {
            val cleanBase64 = if (base64Data.contains(",")) {
                base64Data.substringAfter(",")
            } else {
                base64Data
            }
            val imageBytes = Base64.decode(cleanBase64, Base64.DEFAULT)

            val resolvedMime = if (mimeType.isNotBlank()) mimeType else "image/png"
            val extension = when {
                resolvedMime.contains("jpeg") || resolvedMime.contains("jpg") -> "jpg"
                resolvedMime.contains("webp") -> "webp"
                else -> "png"
            }
            val finalName = if (fileName.contains(".")) fileName else "$fileName.$extension"

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val contentValues = ContentValues().apply {
                    put(MediaStore.MediaColumns.DISPLAY_NAME, finalName)
                    put(MediaStore.MediaColumns.MIME_TYPE, resolvedMime)
                    put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/ImageToolbox")
                    put(MediaStore.MediaColumns.IS_PENDING, 1)
                }

                val resolver = activity.contentResolver
                val uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, contentValues)
                    ?: return "ERROR: Failed to create MediaStore entry"

                resolver.openOutputStream(uri)?.use { stream ->
                    stream.write(imageBytes)
                    stream.flush()
                }

                contentValues.clear()
                contentValues.put(MediaStore.MediaColumns.IS_PENDING, 0)
                resolver.update(uri, contentValues, null, null)

                mainHandler.post {
                    Toast.makeText(activity, "Kaydedildi: Pictures/ImageToolbox/$finalName", Toast.LENGTH_LONG).show()
                }
                return "SUCCESS: Pictures/ImageToolbox/$finalName"
            } else {
                val picturesDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES)
                val targetDir = File(picturesDir, "ImageToolbox")
                if (!targetDir.exists()) {
                    targetDir.mkdirs()
                }
                val destFile = File(targetDir, finalName)
                FileOutputStream(destFile).use { out ->
                    out.write(imageBytes)
                    out.flush()
                }

                // Media scanner trigger
                val mediaScanIntent = Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE).apply {
                    data = Uri.fromFile(destFile)
                }
                activity.sendBroadcast(mediaScanIntent)

                mainHandler.post {
                    Toast.makeText(activity, "Kaydedildi: ${destFile.absolutePath}", Toast.LENGTH_LONG).show()
                }
                return "SUCCESS: ${destFile.absolutePath}"
            }
        } catch (e: Exception) {
            e.printStackTrace()
            mainHandler.post {
                Toast.makeText(activity, "Kaydetme hatası: ${e.message}", Toast.LENGTH_LONG).show()
            }
            return "ERROR: ${e.message}"
        }
    }

    @JavascriptInterface
    fun shareImage(base64Data: String, fileName: String, mimeType: String) {
        try {
            val cleanBase64 = if (base64Data.contains(",")) {
                base64Data.substringAfter(",")
            } else {
                base64Data
            }
            val imageBytes = Base64.decode(cleanBase64, Base64.DEFAULT)

            val resolvedMime = if (mimeType.isNotBlank()) mimeType else "image/png"
            val cacheDir = File(activity.cacheDir, "images")
            if (!cacheDir.exists()) cacheDir.mkdirs()

            val tempFile = File(cacheDir, fileName)
            FileOutputStream(tempFile).use { stream ->
                stream.write(imageBytes)
                stream.flush()
            }

            val uri = FileProvider.getUriForFile(
                activity,
                "${activity.packageName}.fileprovider",
                tempFile
            )

            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                type = resolvedMime
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }

            mainHandler.post {
                activity.startActivity(Intent.createChooser(shareIntent, "Görseli Paylaş"))
            }
        } catch (e: Exception) {
            e.printStackTrace()
            mainHandler.post {
                Toast.makeText(activity, "Paylaşım hatası: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    @JavascriptInterface
    fun copyToClipboard(label: String, text: String) {
        mainHandler.post {
            val clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText(label, text)
            clipboard.setPrimaryClip(clip)
            Toast.makeText(activity, "$label kopyalandı: $text", Toast.LENGTH_SHORT).show()
        }
    }

    @JavascriptInterface
    fun showToast(message: String) {
        mainHandler.post {
            Toast.makeText(activity, message, Toast.LENGTH_SHORT).show()
        }
    }
}
