import json
import os
from urllib import request

from reoptjl.src.vietnam import build_evn_tariff


def build_example_payload(tou_schedule="current"):
    tariff = build_evn_tariff(
        year=2025,
        voltage_level="22-110kV",
        currency="usd",
        exchange_rate_vnd_per_usd=25000,
        tou_schedule=tou_schedule
    )

    return {
        "Settings": {
            "time_steps_per_hour": 1,
        },
        "Site": {
            "latitude": 10.8231,
            "longitude": 106.6297,
        },
        "ElectricLoad": {
            "year": 2025,
            "loads_kw": [500.0] * 8760,
        },
        "ElectricTariff": tariff,
        "Financial": {
            "analysis_years": 25,
        },
        "PV": {
            "max_kw": 1000.0,
        },
        "ElectricStorage": {
            "max_kw": 500.0,
            "max_kwh": 2000.0,
        },
    }


def submit_example(url):
    payload = json.dumps(build_example_payload()).encode("utf-8")
    post_request = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with request.urlopen(post_request) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    api_url = os.environ.get("REOPT_API_URL", "http://localhost:8000/v3/job/")
    print(json.dumps(submit_example(api_url), indent=2))
