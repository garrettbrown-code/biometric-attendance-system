package com.garrettbrown.biometricattendance

import androidx.test.ext.junit.rules.ActivityScenarioRule
import org.junit.Rule
import org.junit.Test

class MainActivityLaunchInstrumentedTest {

    @get:Rule
    val scenarioRule = ActivityScenarioRule(MainActivity::class.java)

    @Test
    fun mainActivity_launches() {
        // If the Activity fails to start, the rule will throw and the test will fail.
        // Intentionally empty.
    }
}