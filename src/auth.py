from enum import Enum
import json
import pkce
import re
import requests


class AuthMethod(Enum):
    TUD_SSO = 0
    OTHER = 1


def auth(username, passw, auth_method=AuthMethod.OTHER):
    print(f"Authenticating with method '{auth_method.name}'...")

    auth_funcs = {
        AuthMethod.TUD_SSO: tud_auth,
        AuthMethod.OTHER: other_auth
    }

    return auth_funcs[auth_method](username, passw)


def tud_auth(netid, passw):
    """
    Authenticates to X through TU Delft's Single Sign-On mechanism.
    """
    auth_url0 = "https://connect.surfconext.nl/oidc/authorize?redirect_uri" + \
                "=https://x.tudelft.nl/oidc/auth-callback&client_id=web-sp" + \
                "orter-frontend.production.delft.delcom.nl&response_type=c" + \
                "ode&state=gS8rpo7j35&scope=openid&access_type=offline&cod" + \
                "e_challenge=2IQEGC4crEF7wPOr9McpbqIi64Z-Polhyn3WGqFOfdU&c" + \
                "ode_challenge_method=S256"
    auth_url1 = "https://engine.surfconext.nl/authentication/idp/process-wayf"
    login_url = "https://login.tudelft.nl/sso/module.php/core/loginuserpass.php?"

    s = requests.Session()

    # Construct required auth payload
    r0 = s.get(auth_url0)
    payload = {
        "ID": extract_auth_idp_id(r0.text),
        "idp": "https://login.tudelft.nl/sso/saml2/idp/metadata.php"
    }

    # Request authorisation through auth_url1, resulting in 2 redirects. The
    # destination's URL contains the AuthState required for login.
    r1 = s.post(auth_url1, data=payload)
    authstate = re.search("AuthState=(.*?)>", r1.text).group(1)

    # Construct login POST request & extract the SAMLResponse
    login_data = {"username": netid, "password": passw, "AuthState": authstate}
    r2 = s.post(login_url, data=login_data)
    saml_resp = extract_saml_response(r2.text, end_char='">')

    # Obtain the second SAML response
    url = "https://engine.surfconext.nl/authentication/sp/consume-assertion"
    r3 = s.post(url, data={"SAMLResponse": saml_resp})
    saml_resp = re.search(r'value=(.*?)">', r3.text).group(1)

    # Obtain session token after login
    saml_url = "https://connect.surfconext.nl/login/saml2/sso/oidcng"
    saml_payload = {
        "SAMLResponse": saml_resp,
    }

    # Option 1: obtain the PKCE challenge through redirects, though we'll miss out on the code verifier
    # r4 = s.post(saml_url, data=saml_payload)  # Handles 2 redirects

    # Option 2: Craft our own PKCE code_verifier and code_challenge
    r4 = s.post(saml_url, data=saml_payload, allow_redirects=False)  # Obtain required cookies
    code_verifier = pkce.generate_code_verifier(length=128)
    code_challenge = pkce.get_code_challenge(code_verifier)
    pkce_state = re.search("state=(.*?)&", r4.headers['location']).group(1)
    pkce_auth_url = f"https://connect.surfconext.nl/oidc/authorize?redirect_uri=https://x.tudelft.nl/oidc/auth-callback&client_id=web-sporter-frontend.production.delft.delcom.nl&response_type=code&state={pkce_state}&scope=openid&access_type=offline&code_challenge={code_challenge}&code_challenge_method=S256"
    r5 = s.get(pkce_auth_url)

    auth_code = re.search("code=(.*?)&", r5.url).group(1)

    token_url = "https://connect.surfconext.nl/oidc/token"
    token_payload = {
        "grant_type": "authorization_code",
        "client_id": "web-sporter-frontend.production.delft.delcom.nl",
        "redirect_uri": "https://x.tudelft.nl/oidc/auth-callback",
        "code": auth_code,
        "code_verifier": code_verifier
    }
    r6 = s.post(token_url, data=token_payload)
    token = r6.json()['access_token']
    s.headers["authorization"] = f"Bearer {token}"
    s.headers["authority"] = "backbone-web-api.production.delft.delcom.nl"

    # TODO: Might be able to obtain member ID from https://backbone-web-api.production.delft.delcom.nl/auth
    r7 = s.get("https://backbone-web-api.production.delft.delcom.nl/auth?cf=0")

    user_info = json.loads(r7.text)
    member_id = user_info["id"] if "id" in user_info else None

    return (s, token, member_id)


def other_auth(email, passw):
    """
    Authenticates through X's authentication portal for non-TUD users.
    """
    auth_url = "https://backbone-web-api.production.delft.delcom.nl/auth"

    s = requests.Session()
    r0 = s.post(auth_url, data={"email": email, "password": passw})

    # Extract and set authorisation headers
    tokens = json.loads(r0.text)
    s.headers["authorization"] = f"Bearer {tokens['access_token']}"
    s.headers["authority"] = "backbone-web-api.production.delft.delcom.nl"

    # Authenticated requests now allow us to obtain user information
    user_info = json.loads(s.get(f"{auth_url}?cf=0").text)
    member_id = user_info["id"] if "id" in user_info else None

    return (s, tokens["access_token"], member_id)


def extract_auth_idp_id(html):
    """
    Extracts and returns the ID string from the `html` content obtained with
    the first request in the authorisation process.
    """
    termination_char = '"/>'
    id_plus_tail = html.split('name="ID" value="')[1]

    return id_plus_tail[:id_plus_tail.index(termination_char)]


def extract_saml_response(html, end_char='">'):
    """
    Extracts and returns the SAMLResponse value from the given `html` content.

    The SAMLResponse value should be terminated with the given `end_char`,
    which should be either `">` or `"/>`.
    """
    saml_doc_str = "name=\"SAMLResponse\" value=\""
    saml_start_idx = html.index(saml_doc_str) + len(saml_doc_str)
    saml_plus_tail = html[saml_start_idx:]

    return saml_plus_tail[:saml_plus_tail.index(end_char)]


def terminate_session(s):
    """
    Cleanly terminates the given session `s` by closing it.
    """
    # TODO: Cleanly log out of X's backend if required
    s.close()
