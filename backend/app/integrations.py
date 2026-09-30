"""Government platform adapters with truthful readiness and credential-safe fallbacks."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _post_json(url: str, payload: dict, headers: dict | None = None, timeout: int = 20) -> dict:
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=request_headers, method="POST")
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class IntegrationAdapter:
    name = "Platform"
    purpose = "catalog discovery"
    platform_url = ""
    credential_envs: tuple[str, ...] = ()
    access_note = "Open the official platform and complete its onboarding for the required service."

    def readiness(self):
        missing = [key for key in self.credential_envs if not os.getenv(key)]
        configured = bool(self.credential_envs) and not missing
        return {
            "name": self.name,
            "purpose": self.purpose,
            "configured": configured,
            "status": "credentials configured; provider access still needs verification" if configured else "setup required",
            "live_enabled": False,
            "platform_url": self.platform_url,
            "required_settings": list(self.credential_envs),
            "missing_settings": missing,
            "next_step": self.access_note if not configured else "Use the provider action to verify authorized access.",
        }

    def discover(self, query=""):
        return {
            **self.readiness(),
            "query": query,
            "results": [],
            "note": "This platform does not expose a configured catalog API in this prototype. Open the official catalog to search; no live request was made.",
        }


class AIKoshAdapter(IntegrationAdapter):
    name = "AIKosh"
    purpose = "discover Indian AI datasets, models and toolkits"
    platform_url = "https://aikosh.indiaai.gov.in/home/datasets/social"
    access_note = "Search the AIKosh public catalogue. Dataset downloads may require registration or follow the dataset licence."


class BhashiniAdapter(IntegrationAdapter):
    name = "BHASHINI"
    purpose = "translate engineer-facing text using an onboarded ULCA pipeline"
    platform_url = "https://bhashini.gov.in/"
    credential_envs = ("BHASHINI_USER_ID", "BHASHINI_API_KEY", "BHASHINI_PIPELINE_ID")
    config_url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"

    def translate(self, text, target_language, source_language="en"):
        readiness = self.readiness()
        if readiness["missing_settings"]:
            return {
                **readiness,
                "translated": False,
                "source_text": text,
                "text": text,
                "source_language": source_language,
                "target_language": target_language,
                "note": "No translation was attempted. Complete BHASHINI onboarding and set all required backend settings.",
            }
        if not text.strip():
            return {**readiness, "translated": False, "error": "Enter text to translate."}

        headers = {"userID": os.environ["BHASHINI_USER_ID"], "ulcaApiKey": os.environ["BHASHINI_API_KEY"]}
        pipeline_id = os.environ["BHASHINI_PIPELINE_ID"]
        config_request = {
            "pipelineTasks": [{"taskType": "translation", "config": {"language": {"sourceLanguage": source_language, "targetLanguage": target_language}}}],
            "pipelineRequestConfig": {"pipelineId": pipeline_id},
        }
        try:
            config = _post_json(self.config_url, config_request, headers)
            task = next((item for item in config.get("pipelineResponseConfig", []) if item.get("taskType") == "translation"), None)
            language_pair = {"sourceLanguage": source_language, "targetLanguage": target_language}
            service = next((item for item in (task or {}).get("config", []) if item.get("language") == language_pair), None)
            endpoint = config.get("pipelineInferenceAPIEndPoint", {})
            if not service or not endpoint.get("callbackUrl") or not endpoint.get("inferenceApiKey"):
                return {**readiness, "translated": False, "error": "BHASHINI returned no matching translation service for this pipeline and language pair."}

            compute_request = {
                "pipelineTasks": [{"taskType": "translation", "config": {"language": language_pair, "serviceId": service["serviceId"]}}],
                "inputData": {"input": [{"source": text}]},
            }
            inference_key = endpoint["inferenceApiKey"]
            translated = _post_json(endpoint["callbackUrl"], compute_request, {inference_key["name"]: inference_key["value"]})
            outputs = translated.get("pipelineResponse", [])
            result_text = outputs[0].get("output", [{}])[0].get("target") if outputs else None
            if not result_text:
                return {**readiness, "translated": False, "error": "BHASHINI responded without translated text."}
            return {**readiness, "live_enabled": True, "status": "connected", "translated": True, "source_language": source_language, "target_language": target_language, "text": result_text, "provider": "BHASHINI ULCA"}
        except HTTPError as exc:
            return {**readiness, "translated": False, "status": "provider_error", "error": f"BHASHINI rejected the request (HTTP {exc.code}); verify pipeline access and language support."}
        except (URLError, TimeoutError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            return {**readiness, "translated": False, "status": "connection_error", "error": f"BHASHINI request failed ({type(exc).__name__}); check connectivity and pipeline configuration."}


class ApiSetuAdapter(IntegrationAdapter):
    name = "API Setu"
    purpose = "discover and subscribe to eligible government APIs"
    platform_url = "https://apisetu.gov.in/"
    access_note = "Browse the marketplace. A consumer account, provider approval and subscription are required before an API can be called."


class DataGovAdapter(IntegrationAdapter):
    name = "data.gov.in"
    purpose = "query public government datasets through the Open Government Data API"
    platform_url = "https://data.gov.in/"
    credential_envs = ("DATAGOV_API_KEY", "DATAGOV_CRUDE_RESOURCE_ID")
    dataset_url = "https://data.gov.in/resource/monthly-indigenous-crude-oil-production"

    def discover(self, query=""):
        if not all(os.getenv(key) for key in self.credential_envs):
            return {**self.readiness(), "query": query, "results": [], "dataset_url": self.dataset_url, "note": "Set the API key and resource ID to query data.gov.in. The public portal link remains available."}
        result = self.crude_production(limit=100)
        records = result.get("records", [])
        q = query.strip().casefold()
        if q:
            records = [row for row in records if q in json.dumps(row, ensure_ascii=False).casefold()]
        return {**result, "query": query, "results": records[:100], "live_enabled": result.get("status") == "connected"}

    def crude_production(self, limit=1000):
        token = os.getenv("DATAGOV_API_KEY")
        resource = os.getenv("DATAGOV_CRUDE_RESOURCE_ID")
        if not token or not resource:
            return {**self.readiness(), "source": "PPAC / data.gov.in", "status": "setup_required", "message": "Set DATAGOV_API_KEY and DATAGOV_CRUDE_RESOURCE_ID to fetch the PPAC Monthly Indigenous Crude Oil Production resource.", "dataset_url": self.dataset_url, "records": []}
        query = urlencode({"api-key": token, "format": "json", "limit": min(max(int(limit), 1), 1000)})
        url = f"https://api.data.gov.in/resource/{resource}?{query}"
        try:
            with urlopen(url, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            records = payload.get("records", [])
            return {**self.readiness(), "configured": True, "live_enabled": True, "source": "PPAC / data.gov.in", "status": "connected", "dataset_url": self.dataset_url, "total": payload.get("total", len(records)), "records": records, "fields": payload.get("field", [])}
        except HTTPError as exc:
            return {**self.readiness(), "source": "PPAC / data.gov.in", "status": "provider_error", "dataset_url": self.dataset_url, "message": f"data.gov.in rejected the request (HTTP {exc.code}); verify the key and resource ID.", "records": []}
        except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            return {**self.readiness(), "source": "PPAC / data.gov.in", "status": "connection_error", "dataset_url": self.dataset_url, "message": f"Source request failed ({type(exc).__name__}); check connectivity and credentials.", "records": []}


ADAPTERS = {adapter.name: adapter() for adapter in (AIKoshAdapter, BhashiniAdapter, ApiSetuAdapter, DataGovAdapter)}
