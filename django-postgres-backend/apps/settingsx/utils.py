from apps.settingsx.models import SettingKV


def _get_int_setting(key: str, default: int) -> int:
    try:
        return int(SettingKV.objects.get(key=key).value)
    except SettingKV.DoesNotExist:
        return int(default)
    except Exception:
        return int(default)


def get_stock_thresholds():
    low = _get_int_setting("low_stock_threshold", 50)
    critical = _get_int_setting("critical_stock_threshold", 10)
    return low, critical
