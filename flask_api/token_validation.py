import time, base64, os
import requests, json
from jwcrypto import jwk, jws, jwt
from dotenv import load_dotenv

load_dotenv()

# AWS Cognito details
USER_POOL_ID = os.getenv("USER_POOL_ID")
APP_CLIENT_ID = os.getenv("APP_CLIENT_ID")
REGION = os.getenv("REGION")

keys_url = (
    f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
)
response = requests.get(keys_url)
keys = response.json()["keys"]


def validate_token(token):
    # Create a JWT object and deserialize the token
    jws_object = jws.JWS()
    jws_object.deserialize(token)

    # Extract the 'kid' from the JOSE header
    kid = jws_object.jose_header["kid"]

    # Find the key that matches the 'kid' in the token
    key = next(key for key in keys if key["kid"] == kid)

    # Construct a jwk object from the key
    jwk_key = jwk.JWK(**key)

    # Verify the token
    jws_object.verify(jwk_key)

    # Extract the claims (payload)
    claims = json.loads(jws_object.payload.decode("utf-8"))

    # Extract the user ID from the 'sub' claim and return it
    user_id = claims["sub"]
    print("token validated successfully!")
    return user_id
