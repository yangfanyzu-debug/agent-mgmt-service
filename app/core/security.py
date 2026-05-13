from fastapi import Header, HTTPException


class CurrentUser:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username


def get_current_user(
    user_id=Header(default=None, alias="user_id"),
    username=Header(default=None, alias="username"),
):
    if not user_id or not username:
        raise HTTPException(status_code=401, detail="Missing RuoYi user headers")
    try:
        parsed_user_id = int(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid RuoYi user id") from exc
    return CurrentUser(user_id=parsed_user_id, username=username)
