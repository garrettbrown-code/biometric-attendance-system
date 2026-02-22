package com.garrettbrown.biometricattendance.feature.student

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.garrettbrown.biometricattendance.core.auth.AuthStore
import com.garrettbrown.biometricattendance.core.camera.FrontCameraCapture
import com.garrettbrown.biometricattendance.core.model.StudentEnrollRequest
import com.garrettbrown.biometricattendance.core.network.ApiClient
import kotlinx.coroutines.launch

@Composable
fun StudentEnrollScreen(
    onSuccess: () -> Unit,
    onBack: () -> Unit,
) {
    val auth = AuthStore.current()
    val api = remember { ApiClient.create(auth) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    var euid by remember { mutableStateOf("") }
    var classCode by remember { mutableStateOf("") }
    var joinCode by remember { mutableStateOf("") }

    var photoB64 by remember { mutableStateOf<String?>(null) }
    var cameraError by remember { mutableStateOf<String?>(null) }

    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }

    val scrollState = rememberScrollState()

    var hasCameraPermission by remember {
        mutableStateOf<Boolean>(
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.CAMERA
            ) == PackageManager.PERMISSION_GRANTED
        )
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
        onResult = { granted: Boolean ->
            hasCameraPermission = granted
        }
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Student Enrollment")
        Text("Enter your class code + join code, then capture a selfie.")

        OutlinedTextField(value = euid, onValueChange = { euid = it }, label = { Text("EUID") })
        OutlinedTextField(value = classCode, onValueChange = { classCode = it }, label = { Text("Class code (csce_4900_500)") })
        OutlinedTextField(value = joinCode, onValueChange = { joinCode = it }, label = { Text("Join code") })

        if (!hasCameraPermission) {
            Button(onClick = { permissionLauncher.launch(Manifest.permission.CAMERA) }) {
                Text("Grant Camera Permission")
            }
        } else if (photoB64.isNullOrBlank()) {
            // Only show the camera preview BEFORE capture
            FrontCameraCapture(
                modifier = Modifier.fillMaxWidth(),
                onCapturedBase64 = {
                    photoB64 = it
                    cameraError = null
                },
                onError = { msg -> cameraError = msg },
            )
        } else {
            // After capture: collapse preview + show confirmation + retake
            Card(
                modifier = Modifier.fillMaxWidth(),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Selfie captured ✅")
                    Button(onClick = { photoB64 = null }) {
                        Text("Retake Selfie")
                    }
                }
            }
        }

        if (cameraError != null) Text("Camera error: $cameraError")

        if (error != null) Text("Error: $error")

        Button(onClick = onBack) { Text("Back") }

        Button(
            enabled = !loading && !photoB64.isNullOrBlank() && euid.isNotBlank() && classCode.isNotBlank() && joinCode.isNotBlank(),
            onClick = {
                loading = true
                error = null
                scope.launch {
                    runCatching {
                        api.enroll(
                            StudentEnrollRequest(
                                euid = euid.trim(),
                                code = classCode.trim(),
                                join_code = joinCode.trim(),
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
                        error = t.message ?: "Enrollment failed"
                    }
                    loading = false
                }
            }
        ) {
            Text(if (loading) "Enrolling..." else "Enroll")
        }
    }
}