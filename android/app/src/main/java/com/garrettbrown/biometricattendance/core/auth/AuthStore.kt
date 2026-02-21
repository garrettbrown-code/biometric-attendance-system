package com.garrettbrown.biometricattendance.core.auth

import android.content.Context
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.platform.LocalContext
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch

private val Context.dataStore by preferencesDataStore(name = "auth")

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
        val Access = stringPreferencesKey("access_token")
        val Refresh = stringPreferencesKey("refresh_token")
        val Role = stringPreferencesKey("role")
        val Euid = stringPreferencesKey("euid")
    }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val _sessionState = MutableStateFlow(Session())
    val sessionState: StateFlow<Session> = _sessionState

    val session: Flow<Session> = context.dataStore.data.map { prefs ->
        Session(
            accessToken = prefs[Keys.Access],
            refreshToken = prefs[Keys.Refresh],
            role = prefs[Keys.Role],
            euid = prefs[Keys.Euid],
        )
    }

    init {
        scope.launch {
            session.collect { s -> _sessionState.value = s }
        }
    }

    suspend fun setSession(access: String, refresh: String, role: String, euid: String) {
        context.dataStore.edit { prefs ->
            prefs[Keys.Access] = access
            prefs[Keys.Refresh] = refresh
            prefs[Keys.Role] = role
            prefs[Keys.Euid] = euid
        }
    }

    suspend fun clear() {
        context.dataStore.edit { prefs ->
            prefs.remove(Keys.Access)
            prefs.remove(Keys.Refresh)
            prefs.remove(Keys.Role)
            prefs.remove(Keys.Euid)
        }
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