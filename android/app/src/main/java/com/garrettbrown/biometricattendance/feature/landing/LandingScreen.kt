package com.garrettbrown.biometricattendance.feature.landing

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import android.util.Log
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.launch
import com.garrettbrown.biometricattendance.core.auth.AuthStore
import com.garrettbrown.biometricattendance.core.network.ApiClient

@Composable
fun LandingScreen(
    onProfessor: () -> Unit,
    onStudent: () -> Unit,
) {
    val auth = AuthStore.current()
    val api = remember { ApiClient.create(auth) }
    val scope = rememberCoroutineScope()
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("Biometric Attendance", style = MaterialTheme.typography.headlineMedium)
        Text("Choose your role to continue.")

        Button(onClick = onStudent) { Text("Student") }
        Button(onClick = onProfessor) { Text("Professor") }
        Button(onClick = {
            scope.launch {
                runCatching { api.health() }
                    .onSuccess { Log.d("HealthCheck", "OK: ${it.status} request_id=${it.request_id}") }
                    .onFailure { Log.e("HealthCheck", "FAILED", it) }
            }
        }) {
            Text("Ping Backend")
        }
    }

}