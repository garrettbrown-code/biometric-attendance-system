package com.garrettbrown.biometricattendance.core.auth

import android.content.Context
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

data class Session(
    val accessToken: String? = null,
    val refreshToken: String? = null,
    val role: String? = null,
    val euid: String? = null,
) {
    val isLoggedIn: Boolean get() = !accessToken.isNullOrBlank() && !role.isNullOrBlank()
}

class AuthStore(private val context: Context) {
    private object Keys {
        const val Access = "access_token"
        const val Refresh = "refresh_token"
        const val Role = "role"
        const val Euid = "euid"
    }

    private val _sessionState = MutableStateFlow(Session())
    val sessionState: StateFlow<Session> = _sessionState

    private val prefs by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        EncryptedSharedPreferences.create(
            context,
            "secure_auth",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    init {
        // load once
        _sessionState.value = Session(
            accessToken = prefs.getString(Keys.Access, null),
            refreshToken = prefs.getString(Keys.Refresh, null),
            role = prefs.getString(Keys.Role, null),
            euid = prefs.getString(Keys.Euid, null),
        )
    }

    fun setSession(access: String, refresh: String, role: String, euid: String) {
        prefs.edit()
            .putString(Keys.Access, access)
            .putString(Keys.Refresh, refresh)
            .putString(Keys.Role, role)
            .putString(Keys.Euid, euid)
            .apply()
        _sessionState.value = Session(access, refresh, role ,euid)
    }

    fun updateTokens(access: String, refresh: String) {
        // Keep role/euid as is
        val current = _sessionState.value
        prefs.edit()
            .putString(Keys.Access, access)
            .putString(Keys.Refresh, refresh)
            .apply()
        _sessionState.value = current.copy(accessToken = access, refreshToken = refresh)
    }

    fun clear() {
        prefs.edit()
            .remove(Keys.Access)
            .remove(Keys.Refresh)
            .remove(Keys.Role)
            .remove(Keys.Euid)
            .apply()
        _sessionState.value = Session()
    }

    // For OkHttp interceptor (sync-ish usage). Avoid heavy calls.
    // This reads from DataStore once; good enough for scaffold.
    fun sessionValue(): Session = _sessionState.value


    companion object {
        private val LocalAuth = staticCompositionLocalOf<AuthStore> {
            error("AuthStore not provided")
        }

        @Composable
        fun current(): AuthStore {
            // Simple singleton per app context for scaffold
            val ctx = LocalContext.current.applicationContext
            return remember(ctx) { AuthStore(ctx) }
        }
    }
}