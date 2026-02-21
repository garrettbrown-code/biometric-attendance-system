package com.garrettbrown.biometricattendance.feature.professor

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
import com.garrettbrown.biometricattendance.core.model.LoginRequest
import com.garrettbrown.biometricattendance.core.network.ApiClient
import kotlinx.coroutines.launch

@Composable
fun ProfessorLoginScreen(
    onSuccess: () -> Unit,
    onBack: () -> Unit,
) {
    val auth = AuthStore.current()
    val api = remember { ApiClient.create(auth) }
    val scope = rememberCoroutineScope()

    var euid by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Professor Login")

        OutlinedTextField(value = euid, onValueChange = { euid = it }, label = { Text("EUID") })
        OutlinedTextField(value = password, onValueChange = { password = it }, label = { Text("Password") })

        if (error != null) Text("Error: $error")

        Button(onClick = onBack) { Text("Back") }

        Button(
            enabled = !loading,
            onClick = {
                loading = true
                error = null
                scope.launch {
                    runCatching {
                        api.login(LoginRequest(euid = euid.trim(), password = password))
                    }.onSuccess { resp ->
                        auth.setSession(
                            access = resp.access_token,
                            refresh = resp.refresh_token,
                            role = "professor",
                            euid = euid.trim(),
                        )
                        onSuccess()
                    }.onFailure { t ->
                        error = t.message ?: "Login failed"
                    }
                    loading = false
                }
            }
        ) {
            Text(if (loading) "Signing in..." else "Sign In")
        }
    }
}