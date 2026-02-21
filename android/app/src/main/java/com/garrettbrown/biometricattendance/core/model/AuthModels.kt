package com.garrettbrown.biometricattendance.core.model

data class LoginRequest(
    val euid: String,
    val password: String,
)

data class StudentEnrollRequest(
    val euid: String,
    val code: String,
    val join_code: String,
    val photo: String,
)

data class FaceLoginRequest(
    val euid: String,
    val photo: String,
)

data class TokenResponse(
    val status: String,
    val access_token: String,
    val refresh_token: String,
    val request_id: String? = null,
)

data class ErrorResponse(
    val status: String? = null,
    val error: String? = null,
    val request_id: String? = null,
)