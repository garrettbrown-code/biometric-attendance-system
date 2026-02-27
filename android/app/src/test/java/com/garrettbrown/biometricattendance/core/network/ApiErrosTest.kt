package com.garrettbrown.biometricattendance.core.network

import com.garrettbrown.biometricattendance.core.model.ErrorResponse
import kotlin.test.Test
import kotlin.test.assertEquals

class ApiErrorsTest {

    @Test
    fun messageFor_includesRequestId_whenPresent() {
        val err = ErrorResponse(
            status = "error",
            error = "Forbidden",
            request_id = "abc-123",
        )

        val msg = ApiErrors.messageFor(403, err)
        assertEquals("Forbidden (request_id=abc-123)", msg)
    }

    @Test
    fun messageFor_fallsBack_whenErrorMissing() {
        val err = ErrorResponse(
            status = "error",
            error = null,
            request_id = null,
        )

        val msg = ApiErrors.messageFor(400, err)
        assertEquals("Request failed", msg)
    }
}