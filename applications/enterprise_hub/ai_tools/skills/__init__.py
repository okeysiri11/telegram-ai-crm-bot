"""Built-in skill templates."""

from applications.enterprise_hub.ai_tools.skills.contract_review import ContractReviewSkill
from applications.enterprise_hub.ai_tools.skills.custom import CustomSkill
from applications.enterprise_hub.ai_tools.skills.document_processing import DocumentProcessingSkill
from applications.enterprise_hub.ai_tools.skills.forecasting import ForecastingSkill
from applications.enterprise_hub.ai_tools.skills.report_generation import ReportGenerationSkill
from applications.enterprise_hub.ai_tools.skills.scheduling import SchedulingSkill

__all__ = [
    "DocumentProcessingSkill",
    "ReportGenerationSkill",
    "ContractReviewSkill",
    "ForecastingSkill",
    "SchedulingSkill",
    "CustomSkill",
]
