import warnings


def test_requests_no_charset_warning():
    """Regression test: importing requests must not emit RequestsDependencyWarning.

    If charset_normalizer is missing from the environment (e.g. removed from
    dependencies), requests will raise this warning, which also appears in the
    PyInstaller binary at runtime.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        import requests  # noqa: F401
