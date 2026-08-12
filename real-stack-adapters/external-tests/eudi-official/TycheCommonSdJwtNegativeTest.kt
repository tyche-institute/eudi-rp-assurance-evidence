@file:Suppress("invisible_member", "invisible_reference")

package eu.europa.ec.eudi.verifier.endpoint.adapter.out.sdjwtvc

import arrow.core.raise.either
import eu.europa.ec.eudi.etsi1196x2.consultation.AttestationClassifications
import eu.europa.ec.eudi.etsi1196x2.consultation.AttestationIdentifierPredicate
import eu.europa.ec.eudi.etsi1196x2.consultation.IsChainTrustedForAttestation
import eu.europa.ec.eudi.etsi1196x2.consultation.IsChainTrustedForContextF
import eu.europa.ec.eudi.sdjwt.vc.TypeMetadataPolicy
import eu.europa.ec.eudi.verifier.endpoint.adapter.out.consultation.Ignored
import eu.europa.ec.eudi.verifier.endpoint.domain.Clock
import eu.europa.ec.eudi.verifier.endpoint.domain.Nonce
import kotlinx.coroutines.test.runTest
import kotlinx.datetime.TimeZone
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue
import kotlin.test.fail
import kotlin.time.Duration.Companion.seconds
import kotlin.time.Instant

class TycheCommonSdJwtNegativeTest {
    private val corpus = Json.parseToJsonElement(
        requireNotNull(javaClass.getResource("/tyche-common-sdjwt-corpus.json")).readText()
    ).jsonObject
    private val cases = corpus.getValue("cases").jsonArray.associateBy {
        it.jsonObject.getValue("case_id").jsonPrimitive.content
    }
    private val context = corpus.getValue("fixed_context").jsonObject
    private val validator = SdJwtVcValidator(
        IsChainTrustedForAttestation(
            IsChainTrustedForContextF.Ignored,
            AttestationClassifications(
                eaAs = mapOf(
                    "tyche-test" to AttestationIdentifierPredicate.sdJwtVcMatching(
                        "^urn:tyche:test:person:1$".toRegex()
                    )
                )
            ),
        ),
        null,
        Clock.fixed(
            Instant.parse(context.getValue("evaluated_at").jsonPrimitive.content),
            TimeZone.UTC,
        ),
        10.seconds,
        TypeMetadataPolicy.NotUsed,
    )

    @Test
    fun acceptsBaselineAndRejectsOnlyIssuerSignatureMutation() = runTest {
        val nonce = Nonce(context.getValue("nonce").jsonPrimitive.content)
        val audience = context.getValue("audience").jsonPrimitive.content
        val baseline = cases.getValue("COMMON-SDJWT-BASELINE-001").jsonObject
            .getValue("presentation").jsonPrimitive.content
        val mutation = cases.getValue("RP_WS_SM_IssuerAuthentication_001").jsonObject
            .getValue("presentation").jsonPrimitive.content

        assertTrue(either { validator.validate(baseline, nonce, audience) }.isRight())

        val errors = assertNotNull(either { validator.validate(mutation, nonce, audience) }.fold(
            ifLeft = { it },
            ifRight = { fail("issuer-signature mutation was accepted") },
        ))
        assertEquals(SdJwtVcValidationErrorCode.ContainsInvalidJwt, errors.head.reason)
        println("TYCHE_OBSERVED_REASON=${errors.head.reason}")
    }
}
