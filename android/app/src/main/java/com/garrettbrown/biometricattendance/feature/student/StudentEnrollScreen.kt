package com.garrettbrown.biometricattendance.feature.student

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.garrettbrown.biometricattendance.core.auth.AuthStore
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

    var euid by remember { mutableStateOf("") }
    var classCode by remember { mutableStateOf("") }
    var joinCode by remember { mutableStateOf("") }

    // Placeholder selfie (next commit will use CameraX)
    var photoB64 by remember { mutableStateOf("PLACEHOLDER_BASE64") }

    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Student Enrollment")
        Text("Enter your class code + join code. Selfie capture comes next commit.")

        OutlinedTextField(value = euid, onValueChange = { euid = it }, label = { Text("EUID") })
        OutlinedTextField(value = classCode, onValueChange = { classCode = it }, label = { Text("Class code (csce_4900_500)") })
        OutlinedTextField(value = joinCode, onValueChange = { joinCode = it }, label = { Text("Join code") })
        OutlinedTextField(value = photoB64, onValueChange = { photoB64 = it }, label = { Text("Photo base64 (temporary)") })

        if (error != null) Text("Error: $error")

        Button(onClick = onBack) { Text("Back") }

        Button(
            enabled = !loading,
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
                                photo = photoB64.trim(),
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