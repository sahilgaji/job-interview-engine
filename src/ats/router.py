from src.ats.greenhouse import GreenhouseATS
from src.ats.personio import PersonioATS
from src.ats.lever import LeverATS
from src.ats.teamtailor import TeamtailorATS
from src.ats.ashby import AshbyATS
from src.ats.recruitee import RecruiteeATS
from src.ats.workable import WorkableATS
from src.ats.softgarden import SoftgardenATS
from src.ats.join_ats import JoinATS

ATS_MODULES = [
    GreenhouseATS(),
    PersonioATS(),
    LeverATS(),
    TeamtailorATS(),
    AshbyATS(),
    RecruiteeATS(),
    WorkableATS(),
    SoftgardenATS(),
    JoinATS(),
]

def get_ats_by_name(name):
    for ats in ATS_MODULES:
        if ats.name == name:
            return ats
    return None

def detect_ats(url, html):
    for ats in ATS_MODULES:
        try:
            if ats.detect(url, html):
                return ats
        except Exception:
            continue
    return None
