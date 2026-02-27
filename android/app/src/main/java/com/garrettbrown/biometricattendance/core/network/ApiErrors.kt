package com.garrettbrown.biometricattendance.core.network

import com.garrettbrown.biometricattendance.core.model.ErrorResponse
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.ResponseBody

class ApiException(
    message: String,
    val httpCode: Int? = null,
    val requestId: String? = null,
) : RuntimeException(message)

object ApiErrors {
    // Lazy init prevents JVM unit tests from failing at class-load time due to Moshi setup.
    private val moshi: Moshi by lazy {
        Moshi.Builder()
            .add(KotlinJsonAdapterFactory())
            .build()
    }
    private val adapter by lazy {
        moshi.adapter(ErrorResponse::class.java)
    }


    fun parseErrorBody(body: ResponseBody?): ErrorResponse? {
        if (body == null) return null
        return runCatching { adapter.fromJson(body.string()) }.getOrNull()
    }

    fun messageFor(code: Int?, err: ErrorResponse?): String {
        val base = err?.error ?: "Request failed"
        val rid = err?.request_id
        return if (!rid.isNullOrBlank()) "$base (request_id=$rid)" else base
    }
}