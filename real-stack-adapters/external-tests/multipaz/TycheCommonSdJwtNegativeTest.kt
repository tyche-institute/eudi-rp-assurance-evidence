package org.multipaz.sdjwt

import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.multipaz.crypto.EcPublicKey
import org.multipaz.crypto.SignatureVerificationException
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.time.Instant

class TycheCommonSdJwtNegativeTest {
    private val corpus = Json.parseToJsonElement(
        requireNotNull(javaClass.getResource("/tyche-common-sdjwt-corpus.json")).readText()
    ).jsonObject
    private val cases = corpus.getValue("cases").jsonArray.associateBy {
        it.jsonObject.getValue("case_id").jsonPrimitive.content
    }
    private val context = corpus.getValue("fixed_context").jsonObject
    private val issuerKey = EcPublicKey.fromJwk(corpus.getValue("issuer_public_jwk").jsonObject)

    @Test
    fun acceptsBaselineAndRejectsOnlyIssuerSignatureMutation() = runTest {
        val expectedNonce = context.getValue("nonce").jsonPrimitive.content
        val expectedAudience = context.getValue("audience").jsonPrimitive.content
        val expectedIat = Instant.fromEpochSeconds(
            context.getValue("iat_epoch_seconds").jsonPrimitive.content.toLong()
        )
        suspend fun verify(caseId: String) = SdJwtKb.fromCompactSerialization(
            cases.getValue(caseId).jsonObject.getValue("presentation").jsonPrimitive.content
        ).verify(
            issuerKey = issuerKey,
            checkNonce = { it == expectedNonce },
            checkAudience = { it == expectedAudience },
            checkCreationTime = { it == expectedIat },
        )

        val payload = verify("COMMON-SDJWT-BASELINE-001")
        assertEquals("urn:tyche:test:person:1", payload.getValue("vct").jsonPrimitive.content)
        val failure = assertFailsWith<SignatureVerificationException> {
            verify("RP_WS_SM_IssuerAuthentication_001")
        }
        assertEquals("Error validating issuer signature", failure.message)
        println("TYCHE_OBSERVED_REASON=SignatureVerificationException: ${failure.message}")
    }
}
