package com.garrettbrown.biometricattendance.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.garrettbrown.biometricattendance.core.auth.AuthStore
import com.garrettbrown.biometricattendance.feature.landing.LandingScreen
import com.garrettbrown.biometricattendance.feature.professor.ProfessorLoginScreen
import com.garrettbrown.biometricattendance.feature.student.StudentEnrollScreen
import com.garrettbrown.biometricattendance.feature.home.HomeScreen
import com.garrettbrown.biometricattendance.feature.settings.SettingsScreen

object Routes {
    const val Landing = "landing"
    const val ProfessorLogin = "prof_login"
    const val StudentEnroll = "student_enroll"
    const val Home = "home"
    const val Settings = "settings"
}

@Composable
fun AppRoot(
    navController: NavHostController = rememberNavController(),
) {
    val auth = AuthStore.current()
    val session by auth.session.collectAsState()

    // If already logged in, go straight to home
    LaunchedEffect(session.isLoggedIn) {
        if (session.isLoggedIn) {
            navController.navigate(Routes.Home) {
                popUpTo(Routes.Landing) { inclusive = true }
            }
        }
    }

    NavHost(navController = navController, startDestination = Routes.Landing) {
        composable(Routes.Landing) {
            LandingScreen(
                onProfessor = { navController.navigate(Routes.ProfessorLogin) },
                onStudent = { navController.navigate(Routes.StudentEnroll) },
            )
        }
        composable(Routes.ProfessorLogin) {
            ProfessorLoginScreen(
                onSuccess = { navController.navigate(Routes.Home) { popUpTo(Routes.Landing) { inclusive = true } } },
                onBack = { navController.popBackStack() },
            )
        }
        composable(Routes.StudentEnroll) {
            StudentEnrollScreen(
                onSuccess = { navController.navigate(Routes.Home) { popUpTo(Routes.Landing) { inclusive = true } } },
                onBack = { navController.popBackStack() },
            )
        }
        composable(Routes.Home) {
            HomeScreen(
                onSettings = { navController.navigate(Routes.Settings) },
            )
        }
        composable(Routes.Settings) {
            SettingsScreen(
                onBack = { navController.popBackStack() },
            )
        }
    }
}