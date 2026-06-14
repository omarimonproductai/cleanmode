import pytest

from mode_cleanup.config import ConfigError, load_config


def test_load_config_ok():
    cfg = load_config(
        {
            "MODE_WORKSPACE": "cooltra",
            "MODE_API_TOKEN": "tok",
            "MODE_API_SECRET": "sec",
        }
    )
    assert cfg.workspace == "cooltra"
    assert cfg.workspace_url == "https://app.mode.com/api/cooltra"


def test_load_config_accepts_mode_secret_alias():
    cfg = load_config(
        {
            "MODE_WORKSPACE": "ecooltra706",
            "MODE_API_TOKEN": "tok",
            "MODE_SECRET": "sec",
        }
    )
    assert cfg.api_secret == "sec"


def test_load_config_missing_raises():
    with pytest.raises(ConfigError) as exc:
        load_config({"MODE_WORKSPACE": "cooltra"})
    assert "MODE_API_TOKEN" in str(exc.value)
    assert "MODE_API_SECRET" in str(exc.value)
