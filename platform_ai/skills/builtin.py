# Built-in example skills.

from __future__ import annotations

from platform_ai.models import TaskType
from platform_ai.skills.models import SkillCategory
from platform_ai.skills.skill_context import SkillContext
from platform_ai.skills.skill_base import AISkill
from platform_ai.skills.skill_registry import skill_registry


class LeadScoringSkill(AISkill):
    skill_id = "lead_scoring"
    name = "Lead Scoring"
    description = "Score sales leads based on profile and behavior signals."
    category = SkillCategory.SCORING.value
    tags = ["sales", "crm", "scoring"]
    capabilities = ["score_lead"]
    task_type = TaskType.CLASSIFICATION

    def required_context(self) -> list[str]:
        return ["lead_profile"]

    def build_prompt(self, ctx: SkillContext) -> str:
        profile = ctx.input.get("lead_profile", ctx.request.get("lead_profile", {}))
        return (
            "Score this sales lead from 0-100. Return JSON: "
            '{"score": number, "tier": "hot|warm|cold", "reasons": [string]}\n'
            f"Profile: {profile}"
        )

    def parse_output(self, raw: str, ctx: SkillContext) -> dict:
        return self.parse_json_output(raw, {"score": 50, "tier": "warm"})


class VinDecoderSkill(AISkill):
    skill_id = "vin_decoder"
    name = "VIN Decoder"
    description = "Decode vehicle identification numbers."
    category = SkillCategory.EXTRACTION.value
    tags = ["auto", "vin", "vehicle"]
    capabilities = ["decode_vin"]
    task_type = TaskType.EXTRACTION

    def required_context(self) -> list[str]:
        return ["vin"]

    def build_prompt(self, ctx: SkillContext) -> str:
        vin = ctx.input.get("vin", "")
        return (
            "Decode this VIN. Return JSON: "
            '{"make": string, "model": string, "year": number, "engine": string}\n'
            f"VIN: {vin}"
        )

    def parse_output(self, raw: str, ctx: SkillContext) -> dict:
        return self.parse_json_output(raw, {"vin": ctx.input.get("vin")})


class DocumentSummarySkill(AISkill):
    skill_id = "document_summary"
    name = "Document Summary"
    description = "Summarize documents and long-form text."
    category = SkillCategory.SUMMARIZATION.value
    tags = ["documents", "summary"]
    capabilities = ["summarize"]
    task_type = TaskType.SUMMARIZATION

    def required_context(self) -> list[str]:
        return ["text"]

    def build_prompt(self, ctx: SkillContext) -> str:
        text = ctx.input.get("text", "")
        return f"Summarize the following document concisely:\n\n{text[:8000]}"


class IntentDetectionSkill(AISkill):
    skill_id = "intent_detection"
    name = "Intent Detection"
    description = "Detect user intent from messages."
    category = SkillCategory.CLASSIFICATION.value
    tags = ["nlp", "intent", "chatbot"]
    capabilities = ["detect_intent"]
    task_type = TaskType.CLASSIFICATION

    def required_context(self) -> list[str]:
        return ["message"]

    def build_prompt(self, ctx: SkillContext) -> str:
        msg = ctx.input.get("message", "")
        return (
            'Detect intent. Return JSON: {"intent": string, "confidence": number}\n'
            f"Message: {msg}"
        )

    def parse_output(self, raw: str, ctx: SkillContext) -> dict:
        return self.parse_json_output(raw, {"intent": "unknown"})


class PriceEstimationSkill(AISkill):
    skill_id = "price_estimation"
    name = "Price Estimation"
    description = "Estimate market prices for goods and services."
    category = SkillCategory.ESTIMATION.value
    tags = ["pricing", "market"]
    capabilities = ["estimate_price"]
    task_type = TaskType.COMPLETION

    def required_context(self) -> list[str]:
        return ["item_description"]

    def build_prompt(self, ctx: SkillContext) -> str:
        desc = ctx.input.get("item_description", "")
        return (
            'Estimate price. Return JSON: {"price_min": number, "price_max": number, "currency": "USD"}\n'
            f"Item: {desc}"
        )

    def parse_output(self, raw: str, ctx: SkillContext) -> dict:
        return self.parse_json_output(raw, {"result": raw})


class OcrWrapperSkill(AISkill):
    skill_id = "ocr_wrapper"
    name = "OCR Wrapper"
    description = "Extract text from images and scanned documents."
    category = SkillCategory.OCR.value
    tags = ["ocr", "vision", "documents"]
    capabilities = ["extract_text"]
    task_type = TaskType.EXTRACTION

    def required_context(self) -> list[str]:
        return ["image_ref"]

    def build_prompt(self, ctx: SkillContext) -> str:
        ref = ctx.input.get("image_ref", "")
        return f"Extract all text from this document reference: {ref}. Return plain text."


class ContractAnalysisSkill(AISkill):
    skill_id = "contract_analysis"
    name = "Contract Analysis"
    description = "Analyze legal contracts for key terms and risks."
    category = SkillCategory.ANALYSIS.value
    tags = ["legal", "contracts"]
    capabilities = ["analyze_contract"]
    permissions = ["ai.use"]
    task_type = TaskType.COMPLETION

    def required_context(self) -> list[str]:
        return ["contract_text"]

    def build_prompt(self, ctx: SkillContext) -> str:
        text = ctx.input.get("contract_text", "")[:10000]
        return (
            "Analyze this contract. Return JSON: "
            '{"parties": [], "key_terms": [], "risks": [], "summary": string}\n'
            f"Contract:\n{text}"
        )

    def parse_output(self, raw: str, ctx: SkillContext) -> dict:
        return self.parse_json_output(raw, {"summary": raw})


class VehicleDescriptionSkill(AISkill):
    skill_id = "vehicle_description"
    name = "Vehicle Description"
    description = "Generate marketing descriptions for vehicles."
    category = SkillCategory.ANALYSIS.value
    tags = ["auto", "marketing"]
    capabilities = ["describe_vehicle"]
    task_type = TaskType.COMPLETION

    def required_context(self) -> list[str]:
        return ["vehicle_specs"]

    def build_prompt(self, ctx: SkillContext) -> str:
        specs = ctx.input.get("vehicle_specs", {})
        return f"Write a compelling vehicle listing description for:\n{specs}"


class InsuranceRecommendationSkill(AISkill):
    skill_id = "insurance_recommendation"
    name = "Insurance Recommendation"
    description = "Recommend insurance products based on profile."
    category = SkillCategory.RECOMMENDATION.value
    tags = ["insurance", "recommendation"]
    capabilities = ["recommend_insurance"]
    task_type = TaskType.COMPLETION

    def required_context(self) -> list[str]:
        return ["profile"]

    def build_prompt(self, ctx: SkillContext) -> str:
        profile = ctx.input.get("profile", {})
        return (
            'Recommend insurance products. Return JSON: {"recommendations": [{"product": string, "reason": string}]}\n'
            f"Profile: {profile}"
        )

    def parse_output(self, raw: str, ctx: SkillContext) -> dict:
        return self.parse_json_output(raw, {"recommendations": []})


class RiskAssessmentSkill(AISkill):
    skill_id = "risk_assessment"
    name = "Risk Assessment"
    description = "Assess business and operational risks."
    category = SkillCategory.RISK.value
    tags = ["risk", "compliance"]
    capabilities = ["assess_risk"]
    task_type = TaskType.COMPLETION

    def required_context(self) -> list[str]:
        return ["scenario"]

    def build_prompt(self, ctx: SkillContext) -> str:
        scenario = ctx.input.get("scenario", "")
        return (
            'Assess risk. Return JSON: {"risk_level": "low|medium|high", "factors": [], "mitigations": []}\n'
            f"Scenario: {scenario}"
        )

    def parse_output(self, raw: str, ctx: SkillContext) -> dict:
        return self.parse_json_output(raw, {"risk_level": "medium"})


_BUILTIN_SKILLS = [
    LeadScoringSkill,
    VinDecoderSkill,
    DocumentSummarySkill,
    IntentDetectionSkill,
    PriceEstimationSkill,
    OcrWrapperSkill,
    ContractAnalysisSkill,
    VehicleDescriptionSkill,
    InsuranceRecommendationSkill,
    RiskAssessmentSkill,
]


def register_all() -> None:
    for skill_cls in _BUILTIN_SKILLS:
        skill_registry.register(skill_cls)
