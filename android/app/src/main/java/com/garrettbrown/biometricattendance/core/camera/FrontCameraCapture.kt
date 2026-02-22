package com.garrettbrown.biometricattendance.core.camera

import android.content.Context
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Rect
import android.graphics.YuvImage
import android.util.Base64
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlinx.coroutines.suspendCancellableCoroutine
import java.io.ByteArrayOutputStream
import kotlin.coroutines.resume

/**
 * CameraX preview + capture, locked to FRONT camera.
 * Captures a selfie and returns a base64(JPEG) string (NO_WRAP).
 */
@Composable
fun FrontCameraCapture(
        modifier: Modifier = Modifier,
        onCapturedBase64: (String) -> Unit,
        onError: (String) -> Unit,
    ) {
        val context = LocalContext.current
        val lifecycleOwner = LocalLifecycleOwner.current
        val previewView = remember { PreviewView(context) }
        var imageCapture by remember { mutableStateOf<ImageCapture?>(null) }
    
        LaunchedEffect(Unit) {
                runCatching {
                        val provider = context.getCameraProvider()
            
                        val preview = androidx.camera.core.Preview.Builder()
                            .build()
                            .also { it.setSurfaceProvider(previewView.surfaceProvider) }
            
                        val capture = ImageCapture.Builder()
                            .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                            .build()
            
                        val selector = CameraSelector.Builder()
                            .requireLensFacing(CameraSelector.LENS_FACING_FRONT)
                            .build()
            
                        provider.unbindAll()
                        provider.bindToLifecycle(lifecycleOwner, selector, preview, capture)
                        imageCapture = capture
                    }.onFailure { t ->
                        onError(t.message ?: "Camera initialization failed")
                    }
            }
    
        Column(modifier = modifier) {
                AndroidView(
                        factory = { previewView },
                        modifier = Modifier
                                    .fillMaxWidth()
                                    .height(280.dp),
                    )
        
                Spacer(Modifier.height(12.dp))
        
                Button(onClick = {
                        val cap = imageCapture
                        if (cap == null) {
                                onError("Camera not ready")
                                return@Button
                            }
            
                        cap.takePicture(
                                ContextCompat.getMainExecutor(context),
                                object : ImageCapture.OnImageCapturedCallback() {
                                        override fun onCaptureSuccess(image: ImageProxy) {
                                                try {
                                                        val bytes = imageProxyToJpegBytes(image)
                                                        val b64 = Base64.encodeToString(bytes, Base64.NO_WRAP)
                                                        onCapturedBase64(b64)
                                                    } catch (t: Throwable) {
                                                        onError(t.message ?: "Capture failed")
                                                    } finally {
                                                        image.close()
                                                    }
                                            }
                    
                                        override fun onError(exception: ImageCaptureException) {
                                                onError(exception.message ?: "Capture error")
                                            }
                                    }
                                    )
                    }) {
                        Text("Capture Selfie")
                    }
            }
    }

private suspend fun Context.getCameraProvider(): ProcessCameraProvider =
        suspendCancellableCoroutine { cont ->
                val future = ProcessCameraProvider.getInstance(this)
                future.addListener(
                        { cont.resume(future.get()) },
                        ContextCompat.getMainExecutor(this)
                            )
            }

/**
 * Many devices return ImageFormat.JPEG from ImageCapture, which has a single plane.
 * If we get JPEG, we can return bytes directly.
 * If we get YUV_420_888, we convert to NV21 then JPEG.
 */
private fun imageProxyToJpegBytes(image: ImageProxy): ByteArray {
    // Fast path: JPEG capture (most common for ImageCapture)
    if (image.format == ImageFormat.JPEG) {
        val buffer = image.planes[0].buffer
        val bytes = ByteArray(buffer.remaining())
        buffer.get(bytes)
        return bytes
    }

    // Fallback: YUV_420_888 capture (3 planes)
    if (image.format != ImageFormat.YUV_420_888 || image.planes.size < 3) {
        throw IllegalStateException("Unsupported image format=${image.format} planes=${image.planes.size}")
    }

    val yBuffer = image.planes[0].buffer
    val uBuffer = image.planes[1].buffer
    val vBuffer = image.planes[2].buffer

    val ySize = yBuffer.remaining()
    val uSize = uBuffer.remaining()
    val vSize = vBuffer.remaining()

    // NV21 format is: Y + interleaved VU
    val nv21 = ByteArray(ySize + uSize + vSize)
    yBuffer.get(nv21, 0, ySize)
    vBuffer.get(nv21, ySize, vSize)
    uBuffer.get(nv21, ySize + vSize, uSize)

    val yuvImage = YuvImage(nv21, ImageFormat.NV21, image.width, image.height, null)
    val out = ByteArrayOutputStream()
    yuvImage.compressToJpeg(Rect(0, 0, image.width, image.height), 85, out)
    return out.toByteArray()
}