from pydantic import BaseModel
from typing import List


class RFPExtraction(BaseModel):

    project_scope: str

    deadlines: List[str]

    staffing_requirements: List[str]

    compliance_requirements: List[str]