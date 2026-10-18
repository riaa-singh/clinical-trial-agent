import requests

BASE = "https://clinicaltrials.gov/api/v2/studies"

def search_trials(condition, phase=None, status=None, max_results=5):
    params = {"query.cond": condition, "pageSize": max_results}
    if phase:
        params["query.term"] = f"AREA[Phase]{phase}"
    if status:
        params["filter.overallStatus"] = status

    r = requests.get(BASE, params=params, timeout=20)
    r.raise_for_status()

    out = []
    for study in r.json().get("studies", []):
        p = study["protocolSection"]
        out.append({
            "nct_id": p["identificationModule"]["nctId"],
            "title": p["identificationModule"]["briefTitle"],
            "status": p["statusModule"]["overallStatus"],
            "phases": p.get("designModule", {}).get("phases", []),
        })
    return out
def get_trial_details(nct_id):
    r = requests.get(f"{BASE}/{nct_id}", timeout=20)
    r.raise_for_status()
    p = r.json()["protocolSection"]

    return {
        "nct_id": nct_id,
        "title": p["identificationModule"]["briefTitle"],
        "status": p["statusModule"]["overallStatus"],
        "phases": p.get("designModule", {}).get("phases", []),
        "enrollment": p.get("designModule", {}).get("enrollmentInfo", {}).get("count"),
        "conditions": p.get("conditionsModule", {}).get("conditions", []),
        "summary": p.get("descriptionModule", {}).get("briefSummary", "")[:800],
        "sponsor": p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name"),
    }


def summarize_eligibility(nct_id):
    r = requests.get(f"{BASE}/{nct_id}", timeout=20)
    r.raise_for_status()
    e = r.json()["protocolSection"].get("eligibilityModule", {})

    return {
        "nct_id": nct_id,
        "criteria": e.get("eligibilityCriteria", "")[:1500],
        "min_age": e.get("minimumAge"),
        "max_age": e.get("maximumAge"),
        "sex": e.get("sex"),
        "healthy_volunteers": e.get("healthyVolunteers"),
    }