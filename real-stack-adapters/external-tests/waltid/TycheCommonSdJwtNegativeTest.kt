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
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class TycheCommonSdJwtNegativeTest {
    private val corpus = Json.parseToJsonElement(
        requireNotNull(javaClass.getResource("/tyche-common-sdjwt-corpus.json")).readText()
    ).jsonObject
    private val cases = corpus.getValue("cases").jsonArray.associateBy {
        it.jsonObject.getValue("case_id").jsonPrimitive.content
    }

    private suspend fun verify(caseId: String): Result<*> {
        val presentation = cases.getValue(caseId).jsonObject
            .getValue("presentation").jsonPrimitive.content
        val (_, credential) = CredentialParser.detectAndParse(presentation)
        assertIs<SdJwtCredential>(credential)
        return CredentialSignaturePolicy().verify(credential)
    }

    @Test
    fun acceptsBaselineAndRejectsOnlyIssuerSignatureMutation() = runTest {
        assertTrue(verify("COMMON-SDJWT-BASELINE-001").isSuccess)
        val failure = assertNotNull(
            verify("RP_WS_SM_IssuerAuthentication_001").exceptionOrNull()
        )
        assertEquals("id.walt.crypto2.jose.InvalidJwsSignatureException", failure::class.qualifiedName)
        assertEquals("Invalid JWS signature", failure.message)
        println("TYCHE_OBSERVED_REASON=${failure::class.qualifiedName}: ${failure.message}")
    }
}
