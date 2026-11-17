from app.core.config import Settings


def test_allowed_user_ids_parse():
    s = Settings(TELEGRAM_ALLOWED_USER_IDS="123, 456")
    assert s.allowed_user_ids() == [123, 456]