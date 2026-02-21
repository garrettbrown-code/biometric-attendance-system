package com.garrettbrown.biometricattendance.core.network

import com.garrettbrown.biometricattendance.core.model.FaceLoginRequest
import com.garrettbrown.biometricattendance.core.model.LoginRequest
import com.garrettbrown.biometricattendance.core.model.StudentEnrollRequest
import com.garrettbrown.biometricattendance.core.model.TokenResponse
import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.GET

data class HealthResponse(
    val status: String,
    val request_id: String
)

interface ApiService {
    @POST("/auth/login")
    suspend fun login(@Body body: LoginRequest): TokenResponse

    @POST("/auth/enroll")
    suspend fun enroll(@Body body: StudentEnrollRequest): TokenResponse

    @POST("/auth/face-login")
    suspend fun faceLogin(@Body body: FaceLoginRequest): TokenResponse

    @GET("/health")
    suspend fun health(): HealthResponse
}