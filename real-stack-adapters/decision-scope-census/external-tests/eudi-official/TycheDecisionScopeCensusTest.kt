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
import kotlin.test.assertTrue
import kotlin.time.Duration.Companion.seconds
import kotlin.time.Instant

class TycheDecisionScopeCensusTest {
    private val corpus = Json.parseToJsonElement(
        requireNotNull(javaClass.getResource("/tyche-decision-scope-corpus.json")).readText()
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
    fun recordsSelectedEntryPointScope() = runTest {
        val nonce = Nonce(context.getValue("nonce").jsonPrimitive.content)
        val audience = context.getValue("audience").jsonPrimitive.content
        for ((caseId, case) in cases.toSortedMap()) {
            val presentation = case.jsonObject.getValue("presentation").jsonPrimitive.content
            val result = either { validator.validate(presentation, nonce, audience) }
            val observed = if (result.isRight()) "ACCEPT" else "REJECT"
            val reason = result.fold(
                ifLeft = { errors -> errors.joinToString("+") { it.reason.toString() } },
                ifRight = { "NONE" },
            )
            println("TYCHE_SCOPE_OBSERVATION|$caseId|$observed|$reason")
            if (caseId == "SCOPE_BASELINE_001") {
                assertTrue(result.isRight(), "$caseId should establish reachability")
            } else {
                assertTrue(result.isLeft(), "$caseId should be refused at this entry point")
            }
        }
    }
}
