package com.garrettbrown.biometricattendance

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.garrettbrown.biometricattendance.ui.AppRoot
import com.garrettbrown.biometricattendance.ui.theme.BiometricAttendanceTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            BiometricAttendanceTheme {
                AppRoot()
            }
        }
    }
}