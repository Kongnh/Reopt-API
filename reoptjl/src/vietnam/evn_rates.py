STANDARD_TOU_MULTIPLIERS = {
    "off_peak": 0.52,
    "normal": 1.0,
    "peak": 1.78,
}


STANDARD_MANUFACTURING_RATES = {
    2025: {
        "source": "EVN retail electricity tariff, Decision 1279/QD-BCT dated 2025-05-09",
        "currency": "vnd",
        "rates_per_kwh": {
            "110kv_and_above": {
                "normal": 1811,
                "off_peak": 1146,
                "peak": 3266,
            },
            "22_to_110kv": {
                "normal": 1833,
                "off_peak": 1190,
                "peak": 3398,
            },
            "6_to_22kv": {
                "normal": 1899,
                "off_peak": 1234,
                "peak": 3508,
            },
            "below_6kv": {
                "normal": 1987,
                "off_peak": 1300,
                "peak": 3640,
            },
        },
    },
}


TWO_COMPONENT_PILOT_RATES = {
    2025: {
        "source": "EVN two-component pilot tariff, paper simulation from 2025-10",
        "currency": "vnd",
        "rates": {
            "110kv_and_above": {
                "capacity_per_kw_month": 209459,
                "energy_per_kwh": {
                    "normal": 1253,
                    "peak": 2162,
                    "off_peak": 843,
                },
            },
            "22_to_110kv": {
                "capacity_per_kw_month": 235414,
                "energy_per_kwh": {
                    "normal": 1275,
                    "peak": 2182,
                    "off_peak": 859,
                },
            },
            "6_to_22kv": {
                "capacity_per_kw_month": 240050,
                "energy_per_kwh": {
                    "normal": 1280,
                    "peak": 2189,
                    "off_peak": 871,
                },
            },
            "below_6kv": {
                "capacity_per_kw_month": 286153,
                "energy_per_kwh": {
                    "normal": 1332,
                    "peak": 2251,
                    "off_peak": 904,
                },
            },
        },
    },
}
