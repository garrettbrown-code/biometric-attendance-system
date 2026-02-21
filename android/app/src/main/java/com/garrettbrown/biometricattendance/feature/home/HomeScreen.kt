package com.garrettbrown.biometricattendance.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.garrettbrown.biometricattendance.core.auth.AuthStore

@Composable
fun HomeScreen(
    onSettings: () -> Unit,
) {
    val auth = AuthStore.current()
    val session by auth.session.collectAsState(initial = com.garrettbrown.biometricattendance.core.auth.Session())

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Home")
        Text("Role: ${session.role ?: "unknown"}")
        Text("EUID: ${session.euid ?: "unknown"}")
        Button(onClick = onSettings) { Text("Settings") }
    }
}