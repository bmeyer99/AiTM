from functools import wraps
from flask import Flask, request
import token_validation as token_validation
testing = False
testing_cognito_id = "eyJraWQiOiJwb3RmM0hXaW5uZ25KelZDRWpacTNodDBESXoxbkJBVUtFZlQreDROR0xJPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJiNDM4ODQ2OC1jMGIxLTcwZWYtZDA5My00OGFkYzhhZmNiODYiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMV9pZDNVUXVvVW8iLCJjbGllbnRfaWQiOiIxZGlnN2RsNjBobjhpMGl0azZwcDBocGVoYiIsIm9yaWdpbl9qdGkiOiI2ODc5YzA5MC05ODNhLTQzNzMtOTk0OS05MWIzNGE5ZjAzMTkiLCJldmVudF9pZCI6IjBkN2ZkZWM2LWU2NGQtNGQ2OC1iM2ExLTkzZjNjOTI4YmU5MiIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3MDc3NTAyNDAsImV4cCI6MTcwNzc1Mzg0MCwiaWF0IjoxNzA3NzUwMjQwLCJqdGkiOiIwYTg1OTg0Mi1lYzRmLTRkM2YtODk5Mi03MjRmYTNiOGFmMjMiLCJ1c2VybmFtZSI6ImI0Mzg4NDY4LWMwYjEtNzBlZi1kMDkzLTQ4YWRjOGFmY2I4NiJ9.wUGVAsmWe7bOvIqYC2Hd_zh1cHYSEfGE03duw0grlU5Y93a5lqzHMmKxB_CWBPdMHWYRAmWCTx0WxeguwHlFkoA2U9z8i-w4bM4h4MyoGV7TGlzCZa3IqJx49oZ3GJaRIuMn1DzlHaEIsm-i6AJZfwTAYkjpBnXmFyrJwSvVHVYPmZi69poHO1ve8WEGiQ_NXvsh3Cft7mc7fBgn5HGB74xuDhehf0Vt7gqZNowCB0tChRWmSZQAHVLPYKOtmwun8d8yQLoIInUksp4H1kCOObPz7yMSXXcR7_STweRChlv3NHxJrz6aLr8tqUogF6LvoBu5c8UGCqXOlXdogGNGSw"


def token_required(f):
    @wraps(f)
    def my_decorator(*args, **kwargs):
        if testing:
            cognito_id = testing_cognito_id
        else:
            token = request.headers.get("Authorization").split()[1]
            cognito_id = token_validation.validate_token(token)
        if not cognito_id:
            return {"message": "Invalid token"}, 401
        return f(cognito_id=cognito_id, *args, **kwargs)

    return my_decorator




# handle exceptions
def handle_exceptions(f):
    @wraps(f)
    def my_decorator(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return {"message": str(e)}, 500

    return my_decorator
