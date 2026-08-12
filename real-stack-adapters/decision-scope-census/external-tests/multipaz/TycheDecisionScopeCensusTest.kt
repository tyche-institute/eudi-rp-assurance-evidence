package org.multipaz.sdjwt

import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.multipaz.crypto.EcPublicKey
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.time.Instant

class TycheDecisionScopeCensusTest {
    private val corpus = Json.parseToJsonElement(
        requireNotNull(javaClass.getResource("/tyche-decision-scope-corpus.json")).readText()
    ).jsonObject
    private val cases = corpus.getValue("cases").jsonArray.associateBy {
        it.jsonObject.getValue("case_id").jsonPrimitive.content
    }
    private val context = corpus.getValue("fixed_context").jsonObject
    private val issuerKey = EcPublicKey.fromJwk(corpus.getValue("issuer_public_jwk").jsonObject)

    @Test
    fun recordsSelectedEntryPointScope() = runTest {
        val expectedNonce = context.getValue("nonce").jsonPrimitive.content
        val expectedAudience = context.getValue("audience").jsonPrimitive.content
        val expectedIat = Instant.fromEpochSeconds(
            context.getValue("iat_epoch_seconds").jsonPrimitive.content.toLong()
        )
        for ((caseId, case) in cases.toSortedMap()) {
            val presentation = case.jsonObject.getValue("presentation").jsonPrimitive.content
            var observed = "ACCEPT"
            var reason = "NONE"
            try {
                SdJwtKb.fromCompactSerialization(presentation).verify(
                    issuerKey = issuerKey,
                    checkNonce = { it == expectedNonce },
                    checkAudience = { it == expectedAudience },
                    checkCreationTime = { it == expectedIat },
                )
            } catch (failure: Throwable) {
                observed = "REJECT"
                reason = "${failure::class.qualifiedName}: ${failure.message ?: "no-message"}"
            }
            println("TYCHE_SCOPE_OBSERVATION|$caseId|$observed|$reason")
            val expected = if (caseId == "SCOPE_BASELINE_001") "ACCEPT" else "REJECT"
            assertEquals(expected, observed, "$caseId had an unexpected observation")
        }
    }
}
