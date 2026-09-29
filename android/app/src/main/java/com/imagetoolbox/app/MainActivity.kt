package com.imagetoolbox.app

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Matrix
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.OpenableColumns
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.exifinterface.media.ExifInterface
import androidx.webkit.WebViewAssetLoader
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var assetLoader: WebViewAssetLoader
    private val mainHandler = Handler(Looper.getMainLooper())
    private lateinit var cacheImagesDir: File

    private val singleImagePicker = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        uri?.let { handleSelectedImage(it) }
    }

    private val multiImagePicker = registerForActivityResult(ActivityResultContracts.GetMultipleContents()) { uris: List<Uri> ->
        if (uris.isNotEmpty()) {
            handleSelectedMultipleImages(uris)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Edge-to-edge dark styling
        window.statusBarColor = Color.parseColor("#121214")
        window.navigationBarColor = Color.parseColor("#121214")

        cacheImagesDir = File(cacheDir, "images")
        if (!cacheImagesDir.exists()) {
            cacheImagesDir.mkdirs()
        }

        webView = WebView(this).apply {
            setBackgroundColor(Color.parseColor("#121214"))
            settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                allowFileAccess = true
                databaseEnabled = true
                useWideViewPort = true
                loadWithOverviewMode = true
                builtInZoomControls = false
                displayZoomControls = false
                cacheMode = WebSettings.LOAD_DEFAULT
            }
        }

        assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .addPathHandler("/cache/", WebViewAssetLoader.InternalStoragePathHandler(this, cacheImagesDir))
            .build()

        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? {
                val response = assetLoader.shouldInterceptRequest(request.url) ?: return null
                val headers = response.responseHeaders?.toMutableMap() ?: mutableMapOf()
                headers["Access-Control-Allow-Origin"] = "*"
                headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
                response.responseHeaders = headers
                return response
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                intent?.let { handleIncomingIntent(it) }
            }
        }

        webView.webChromeClient = WebChromeClient()
        webView.addJavascriptInterface(WebAppInterface(this), "AndroidBridge")

        setContentView(webView)
        webView.loadUrl("https://appassets.androidplatform.net/assets/www/index.html")
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        intent?.let { handleIncomingIntent(it) }
    }

    private fun handleIncomingIntent(intent: Intent) {
        if (intent.action == Intent.ACTION_SEND && intent.type?.startsWith("image/") == true) {
            @Suppress("DEPRECATION")
            val imageUri = intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)
            imageUri?.let { handleSelectedImage(it) }
        }
    }

    fun launchPhotoPicker() {
        singleImagePicker.launch("image/*")
    }

    fun launchMultiPhotoPicker() {
        multiImagePicker.launch("image/*")
    }

    private fun handleSelectedImage(uri: Uri) {
        Thread {
            try {
                val contentResolver = contentResolver
                var fileName = "image.jpg"
                var originalFileSize = 0L

                contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                    val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    val sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE)
                    if (cursor.moveToFirst()) {
                        if (nameIndex != -1) fileName = cursor.getString(nameIndex) ?: "image.jpg"
                        if (sizeIndex != -1) originalFileSize = cursor.getLong(sizeIndex)
                    }
                }

                // 1. Decode bitmap
                val inputStream: InputStream = contentResolver.openInputStream(uri) ?: return@Thread
                val decodedBitmap = BitmapFactory.decodeStream(inputStream)
                inputStream.close()

                if (decodedBitmap == null) {
                    mainHandler.post {
                        Toast.makeText(this@MainActivity, "Görsel yüklenemedi / format desteklenmiyor", Toast.LENGTH_SHORT).show()
                    }
                    return@Thread
                }

                // 2. EXIF Orientation correction
                val rotationDegrees = try {
                    contentResolver.openInputStream(uri)?.use { stream ->
                        val exif = ExifInterface(stream)
                        when (exif.getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL)) {
                            ExifInterface.ORIENTATION_ROTATE_90 -> 90
                            ExifInterface.ORIENTATION_ROTATE_180 -> 180
                            ExifInterface.ORIENTATION_ROTATE_270 -> 270
                            else -> 0
                        }
                    } ?: 0
                } catch (e: Exception) {
                    0
                }

                val orientedBitmap = if (rotationDegrees != 0) {
                    val matrix = Matrix().apply { postRotate(rotationDegrees.toFloat()) }
                    Bitmap.createBitmap(decodedBitmap, 0, 0, decodedBitmap.width, decodedBitmap.height, matrix, true)
                } else {
                    decodedBitmap
                }

                // 3. Cap max dimension to 3840px (4K) to avoid mobile GPU canvas texture crash
                val maxDimension = 3840
                val finalBitmap = if (orientedBitmap.width > maxDimension || orientedBitmap.height > maxDimension) {
                    val scale = maxDimension.toFloat() / Math.max(orientedBitmap.width, orientedBitmap.height)
                    val targetW = (orientedBitmap.width * scale).toInt()
                    val targetH = (orientedBitmap.height * scale).toInt()
                    Bitmap.createScaledBitmap(orientedBitmap, targetW, targetH, true)
                } else {
                    orientedBitmap
                }

                // 4. Save to cacheImagesDir
                val hasAlpha = finalBitmap.hasAlpha()
                val extension = if (hasAlpha) "png" else "jpg"
                val mimeType = if (hasAlpha) "image/png" else "image/jpeg"
                val targetFile = File(cacheImagesDir, "active_image.$extension")

                FileOutputStream(targetFile).use { out ->
                    if (hasAlpha) {
                        finalBitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
                    } else {
                        finalBitmap.compress(Bitmap.CompressFormat.JPEG, 92, out)
                    }
                    out.flush()
                }

                val fileSize = if (originalFileSize > 0) originalFileSize else targetFile.length()
                val cacheUrl = "https://appassets.androidplatform.net/cache/active_image.$extension?t=${System.currentTimeMillis()}"

                val jsCode = """
                    if (window.onImageLoadedFromAndroid) {
                        window.onImageLoadedFromAndroid('$cacheUrl', '${escapeJs(fileName)}', $fileSize, '$mimeType');
                    }
                """.trimIndent()

                mainHandler.post {
                    webView.evaluateJavascript(jsCode, null)
                }
            } catch (e: Exception) {
                e.printStackTrace()
                mainHandler.post {
                    Toast.makeText(this@MainActivity, "Görsel yükleme hatası: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }.start()
    }

    private fun handleSelectedMultipleImages(uris: List<Uri>) {
        Thread {
            try {
                val contentResolver = contentResolver
                val itemsJson = StringBuilder("[")

                uris.forEachIndexed { index, uri ->
                    var fileName = "image_$index.jpg"
                    var originalFileSize = 0L

                    contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                        val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                        val sizeIndex = cursor.getColumnIndex(OpenableColumns.SIZE)
                        if (cursor.moveToFirst()) {
                            if (nameIndex != -1) fileName = cursor.getString(nameIndex) ?: "image_$index.jpg"
                            if (sizeIndex != -1) originalFileSize = cursor.getLong(sizeIndex)
                        }
                    }

                    val inputStream = contentResolver.openInputStream(uri) ?: return@forEachIndexed
                    val decoded = BitmapFactory.decodeStream(inputStream)
                    inputStream.close()

                    if (decoded != null) {
                        val maxDimension = 2560
                        val finalBmp = if (decoded.width > maxDimension || decoded.height > maxDimension) {
                            val scale = maxDimension.toFloat() / Math.max(decoded.width, decoded.height)
                            Bitmap.createScaledBitmap(decoded, (decoded.width * scale).toInt(), (decoded.height * scale).toInt(), true)
                        } else {
                            decoded
                        }

                        val hasAlpha = finalBmp.hasAlpha()
                        val ext = if (hasAlpha) "png" else "jpg"
                        val mime = if (hasAlpha) "image/png" else "image/jpeg"
                        val targetFile = File(cacheImagesDir, "batch_${index}.$ext")

                        FileOutputStream(targetFile).use { out ->
                            if (hasAlpha) {
                                finalBmp.compress(Bitmap.CompressFormat.PNG, 100, out)
                            } else {
                                finalBmp.compress(Bitmap.CompressFormat.JPEG, 90, out)
                            }
                            out.flush()
                        }

                        val fSize = if (originalFileSize > 0) originalFileSize else targetFile.length()
                        val cacheUrl = "https://appassets.androidplatform.net/cache/batch_${index}.$ext?t=${System.currentTimeMillis()}"

                        if (itemsJson.length > 1) itemsJson.append(",")
                        itemsJson.append("""{"name":"${escapeJs(fileName)}","size":$fSize,"mime":"$mime","url":"$cacheUrl"}""")
                    }
                }
                itemsJson.append("]")

                val jsCode = """
                    if (window.onBatchImagesLoadedFromAndroid) {
                        window.onBatchImagesLoadedFromAndroid($itemsJson);
                    }
                """.trimIndent()

                mainHandler.post {
                    webView.evaluateJavascript(jsCode, null)
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }.start()
    }

    private fun escapeJs(str: String): String {
        return str.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        val jsCode = "if (window.onAndroidBackPressed) { window.onAndroidBackPressed(); } else { false; }"
        webView.evaluateJavascript(jsCode) { result ->
            if (result != "true") {
                @Suppress("DEPRECATION")
                super.onBackPressed()
            }
        }
    }
}
