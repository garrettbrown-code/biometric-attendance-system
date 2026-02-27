package com.garrettbrown.biometricattendance.core.network

import retrofit2.HttpException

suspend inline fun <T> safeApiCall(crossinline block: suspend () -> T): T {
    try {
        return block()
    } catch (e: HttpException) {
        val err = ApiErrors.parseErrorBody(e.response()?.errorBody())
        throw ApiException(
            message = ApiErrors.messageFor(e.code(), err),
            httpCode = e.code(),
            requestId = err?.request_id,
        )
    }
}