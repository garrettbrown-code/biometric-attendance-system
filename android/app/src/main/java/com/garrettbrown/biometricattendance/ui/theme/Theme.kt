package com.garrettbrown.biometricattendance.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember

@Composable
fun BiometricAttendanceTheme(
    content: @Composable () -> Unit
) {
    val isDark = remember { mutableStateOf(false) }
    val colors = if (isDark.value) darkColorScheme() else lightColorScheme()
    MaterialTheme(
        colorScheme = colors,
        content = content
    )
}