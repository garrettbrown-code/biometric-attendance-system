package com.garrettbrown.biometricattendance.core.network

import com.garrettbrown.biometricattendance.core.model.RefreshRequest
import com.garrettbrown.biometricattendance.core.model.TokenResponse
import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.POST

interface AuthApiService {
    @POST("/auth/refresh")
    fun refresh(@Body body: RefreshRequest): Call<TokenResponse>
}
