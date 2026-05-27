import io
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from proforma_vietnam import pvwatts_client


class PVWattsClientTests(TestCase):

    def setUp(self):
        self.cache_dir = Path(tempfile.mkdtemp()) / "pvwatts_cache"
        cache_patcher = patch.object(pvwatts_client, "CACHE_DIR", self.cache_dir)
        cache_patcher.start()
        self.addCleanup(cache_patcher.stop)

    def test_fetch_returns_normalized_8760_series_and_caches_result(self):
        ac_w = [200.0] * 8760  # 200 W per 1 kW DC → 0.2 production factor
        urlopen = _stub_urlopen({"outputs": {"ac": ac_w}, "errors": []})

        with patch.object(pvwatts_client.request, "urlopen", urlopen):
            series = pvwatts_client.fetch_production_factor_series(
                latitude=10.0,
                longitude=106.0,
                api_key="dummy-key",
            )

        self.assertEqual(len(series), 8760)
        self.assertEqual(series[0], 0.2)
        self.assertEqual(urlopen.call_count, 1)
        cached_files = list(self.cache_dir.glob("*.json"))
        self.assertEqual(len(cached_files), 1)

    def test_fetch_uses_cache_on_repeat_call_with_same_params(self):
        ac_w = [100.0] * 8760
        urlopen = _stub_urlopen({"outputs": {"ac": ac_w}, "errors": []})

        with patch.object(pvwatts_client.request, "urlopen", urlopen):
            first = pvwatts_client.fetch_production_factor_series(
                latitude=10.0,
                longitude=106.0,
                api_key="dummy-key",
            )
            second = pvwatts_client.fetch_production_factor_series(
                latitude=10.0,
                longitude=106.0,
                api_key="dummy-key",
            )

        self.assertEqual(first, second)
        self.assertEqual(urlopen.call_count, 1)

    def test_fetch_recomputes_when_override_params_differ(self):
        ac_w = [100.0] * 8760
        urlopen = _stub_urlopen({"outputs": {"ac": ac_w}, "errors": []})

        with patch.object(pvwatts_client.request, "urlopen", urlopen):
            pvwatts_client.fetch_production_factor_series(
                latitude=10.0,
                longitude=106.0,
                api_key="dummy-key",
            )
            pvwatts_client.fetch_production_factor_series(
                latitude=10.0,
                longitude=106.0,
                overrides={"tilt": 20},
                api_key="dummy-key",
            )

        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(len(list(self.cache_dir.glob("*.json"))), 2)

    def test_query_sends_default_pvwatts_params_and_overrides(self):
        ac_w = [100.0] * 8760
        urlopen = _stub_urlopen({"outputs": {"ac": ac_w}, "errors": []})

        with patch.object(pvwatts_client.request, "urlopen", urlopen):
            pvwatts_client.fetch_production_factor_series(
                latitude=10.0,
                longitude=106.0,
                overrides={"tilt": 15, "azimuth": 170},
                api_key="dummy-key",
            )

        request_obj = urlopen.call_args.args[0]
        url = request_obj if isinstance(request_obj, str) else request_obj
        # _stub_urlopen captures the URL as a string in call_args
        self.assertIn("tilt=15", url)
        self.assertIn("azimuth=170", url)
        self.assertIn("array_type=1", url)
        self.assertIn("module_type=0", url)
        self.assertIn("losses=14", url)
        self.assertIn("dc_ac_ratio=1.2", url)
        self.assertIn("timeframe=hourly", url)
        self.assertIn("system_capacity=1", url)

    def test_rejects_unsupported_override_keys(self):
        with self.assertRaises(ValueError) as context:
            pvwatts_client.fetch_production_factor_series(
                latitude=10.0,
                longitude=106.0,
                overrides={"tilt": 15, "bogus": 1},
                api_key="dummy-key",
            )

        self.assertIn("bogus", str(context.exception))

    def test_raises_when_pvwatts_returns_errors(self):
        urlopen = _stub_urlopen({"outputs": {"ac": []}, "errors": ["lat out of range"]})

        with patch.object(pvwatts_client.request, "urlopen", urlopen):
            with self.assertRaises(RuntimeError):
                pvwatts_client.fetch_production_factor_series(
                    latitude=10.0,
                    longitude=106.0,
                    api_key="dummy-key",
                )

    def test_raises_when_api_key_unavailable(self):
        with patch.dict("os.environ", {}, clear=False):
            os_env_patch = patch.dict("os.environ", clear=True)
            os_env_patch.start()
            self.addCleanup(os_env_patch.stop)
            env_patch = patch.object(pvwatts_client, "ENV_FILE", Path("/nonexistent/.env"))
            env_patch.start()
            self.addCleanup(env_patch.stop)

            with self.assertRaises(RuntimeError):
                pvwatts_client.fetch_production_factor_series(
                    latitude=10.0,
                    longitude=106.0,
                )


def _stub_urlopen(response_body):
    """Return a mock urlopen that yields ``response_body`` JSON-encoded.

    The mock records the URL string from positional args[0] so tests can
    assert on the query parameters sent.
    """
    payload = json.dumps(response_body).encode("utf-8")

    def fake_urlopen(url, *args, **kwargs):
        return _ContextResponse(payload)

    from unittest.mock import MagicMock
    mock = MagicMock(side_effect=fake_urlopen)
    return mock


class _ContextResponse:
    def __init__(self, payload):
        self._buffer = io.BytesIO(payload)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._buffer.read()
