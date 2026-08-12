package id.walt.policies2.vc

import id.walt.credentials.CredentialParser
import id.walt.credentials.formats.SdJwtCredential
import id.walt.policies2.vc.policies.CredentialSignaturePolicy
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs

class TycheDecisionScopeCensusTest {
    private val corpus = Json.parseToJsonElement(
        requireNotNull(javaClass.getResource("/tyche-decision-scope-corpus.json")).readText()
    ).jsonObject
    private val cases = corpus.getValue("cases").jsonArray.associateBy {
        it.jsonObject.getValue("case_id").jsonPrimitive.content
    }

    private suspend fun verify(presentation: String): Result<*> {
        val (_, credential) = CredentialParser.detectAndParse(presentation)
        assertIs<SdJwtCredential>(credential)
        return CredentialSignaturePolicy().verify(credential)
    }

    @Test
    fun recordsSelectedEntryPointScope() = runTest {
        for ((caseId, case) in cases.toSortedMap()) {
            val presentation = case.jsonObject.getValue("presentation").jsonPrimitive.content
            val result = verify(presentation)
            val observed = if (result.isSuccess) "ACCEPT" else "REJECT"
            val failure = result.exceptionOrNull()
            val reason = if (failure == null) {
                "NONE"
            } else {
                "${failure::class.qualifiedName}: ${failure.message ?: "no-message"}"
            }
            println("TYCHE_SCOPE_OBSERVATION|$caseId|$observed|$reason")
            val expected = if (caseId == "SCOPE_ISSUER_SIGNATURE_INVALID_001") "REJECT" else "ACCEPT"
            assertEquals(expected, observed, "$caseId had an unexpected observation")
        }
    }
}
