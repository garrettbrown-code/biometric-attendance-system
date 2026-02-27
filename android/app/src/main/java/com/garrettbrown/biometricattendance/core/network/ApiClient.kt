package com.garrettbrown.biometricattendance.core.network

import com.garrettbrown.biometricattendance.BuildConfig
import com.garrettbrown.biometricattendance.core.auth.AuthStore
import com.garrettbrown.biometricattendance.core.model.RefreshRequest
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.Authenticator
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory

object ApiClient {
    private val moshi = Moshi.Builder()
        .add(KotlinJsonAdapterFactory())
        .build()

    private fun authInterceptor(auth: AuthStore): Interceptor = Interceptor { chain ->
        val req = chain.request()
        val token = auth.sessionValue().accessToken
        val newReq = if (!token.isNullOrBlank()) {
            req.newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        } else req
        chain.proceed(newReq)
    }

    private fun tokenAuthenticator(auth: AuthStore): Authenticator = object : Authenticator {
        override fun authenticate(route: Route?, response: Response): Request? {
            // avoid infinite loops
            if (responseCount(response) >= 2) return null

            val refresh = auth.sessionValue().refreshToken ?: return null

            val authApi = createAuthApi()
            val refreshResp = runCatching {
                authApi.refresh(RefreshRequest(refresh_token = refresh)).execute()
            }.getOrNull() ?: return null

            if (!refreshResp.isSuccessful) return null
            val body = refreshResp.body() ?: return null
            if (body.status != "success") return null

            auth.updateTokens(access = body.access_token, refresh = body.refresh_token)

            return response.request.newBuilder()
                .header("Authorization", "Bearer ${body.access_token}")
                .build()
        }

        private fun responseCount(response: Response): Int {
            var r: Response? = response
            var count = 1
            while (r?.priorResponse != null) {
                count++
                r = r.priorResponse
            }
            return count
        }
    }

    private fun createAuthApi(): AuthApiService {
        val retrofit = Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
        return retrofit.create(AuthApiService::class.java)
    }


    fun create(auth: AuthStore): ApiService {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(authInterceptor(auth))
            .authenticator(tokenAuthenticator(auth))
            .addInterceptor(logging)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(client)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()

        return retrofit.create(ApiService::class.java)
    }
}