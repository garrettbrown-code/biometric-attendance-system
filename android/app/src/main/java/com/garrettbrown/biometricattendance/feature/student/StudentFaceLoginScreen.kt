package com.garrettbrown.biometricattendance.feature.student

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.garrettbrown.biometricattendance.core.auth.AuthStore
import com.garrettbrown.biometricattendance.core.camera.FrontCameraCapture
import com.garrettbrown.biometricattendance.core.model.FaceLoginRequest
import com.garrettbrown.biometricattendance.core.network.ApiClient
import kotlinx.coroutines.launch

@Composable
fun StudentFaceLoginScreen(
    onSuccess: () -> Unit,
    onBack: () -> Unit,
) {
    val auth = AuthStore.current()
    val api = remember { ApiClient.create(auth) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    var euid by remember { mutableStateOf("") }
    var photoB64 by remember { mutableStateOf<String?>(null) }
    var cameraError by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }

    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
        )
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
        onResult = { granted -> hasCameraPermission = granted }
    )

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Student Face Login")

        OutlinedTextField(value = euid, onValueChange = { euid = it }, label = { Text("EUID") })

        if (!hasCameraPermission) {
            Button(onClick = { permissionLauncher.launch(Manifest.permission.CAMERA) }) {
                Text("Grant Camera Permission")
            }
        } else {
            FrontCameraCapture(
                onCapturedBase64 = {
                    photoB64 = it
                    cameraError = null
                },
                onError = { msg -> cameraError = msg },
            )
        }

        if (photoB64 != null) Text("Selfie captured ✅")
        if (cameraError != null) Text("Camera error: $cameraError")
        if (error != null) Text("Error: $error")

        Button(onClick = onBack) { Text("Back") }

        Button(
            enabled = !loading && !photoB64.isNullOrBlank() && euid.isNotBlank(),
            onClick = {
                loading = true
                error = null
                scope.launch {
                    runCatching {
                        api.faceLogin(
                            FaceLoginRequest(
                                euid = euid.trim(),
                                photo = photoB64!!.trim(),
                            )
                        )
                    }.onSuccess { resp ->
                        auth.setSession(
                            access = resp.access_token,
                            refresh = resp.refresh_token,
                            role = "student",
                            euid = euid.trim(),
                        )
                        onSuccess()
                    }.onFailure { t ->
                        error = t.message ?: "Face login failed"
                    }
                    loading = false
                }
            }
        ) {
            Text(if (loading) "Logging in..." else "Log In")
        }
    }
}