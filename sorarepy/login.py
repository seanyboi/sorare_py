# AUTOGENERATED! DO NOT EDIT! File to edit: 00_login.ipynb (unless otherwise specified).

__all__ = ['LoginSorare']

# Cell
import requests
import json
import bcrypt
from typing import Dict, Tuple

# Internal Cell
class LoginError(Exception):
    pass

# Cell
class LoginSorare():
    def __init__(self, app_name: str, email: str, password: str, two_factor: str = None):
        '''
        Wrapper to allow users to retreieve their JWT and club name.

        `app_name`: Name you wish to call your app.
       <br/>`email`: Email address you use to login to your Sorare account.
       <br/>`password`: Password you use to login to your Sorare account.
       `two_factor`: Two factor you use to login to your Sorare account.
        '''
        if not isinstance(app_name, str):
            raise TypeError("App name must be a string")
        if not isinstance(email, str):
            raise TypeError("Email name must be a string")
        if not isinstance(password, str):
            raise TypeError("Password name must be a string")
        if not isinstance(two_factor, str):
            raise TypeError("Two factor name must be a string")

        self.app_name = app_name
        self.email = email
        self.password = password
        self.two_factor = two_factor


    def post_query(func) -> Dict:
        def run_post_query(self, *args, **kwargs):
            try:
                query, variables = func(self)
                return requests.post(kwargs["url"],
                             json={'query': query, 'OperationName': kwargs["ops_name"], 'variables': variables},
                             headers=kwargs["headers"])
            except:
                LoginError("Please check email, password or two factor token")
        return run_post_query


    @post_query
    def login_query(self) -> Tuple[str, str]:
        if bool(self.two_factor):
            variables = {
              "input": {
                "otpSessionChallenge": self.opt_challenge,
                "otpAttempt": self.two_factor
              }
            }
        else:
            variables = {
              "input": {
                "email": self.email,
                "password": self.retrieve_password()
              }
            }

        query = f"""
            mutation SignInMutation($input: signInInput!){{
              signIn(input: $input) {{
                currentUser {{
                  slug
                  jwtToken(aud: "{self.app_name}") {{
                    token
                    expiredAt
                  }}
                }}
                errors {{
                  message
                }}
              }}
            }}
        """
        return query, variables

    @post_query
    def two_factor_query(self) -> Tuple[str, str]:

        variables = {
              "input": {
                "email": self.email,
                "password": self.retrieve_password()
              }
        }

        query = f"""
            mutation SignInMutation($input: signInInput!) {{
              signIn(input: $input) {{
                currentUser {{
                  slug
                  jwtToken(aud: "{self.app_name}") {{
                    token
                    expiredAt
                  }}
                }}
                otpSessionChallenge
                errors {{
                  message
                }}
              }}
            }}
        """

        return query, variables

    def retrieve_password(self) -> str:
        r = requests.get(f"https://api.sorare.com/api/v1/users/{self.email}")
        response = json.loads(r.content)
        salt = response["salt"].encode("utf-8")
        hashed_password = bcrypt.hashpw(self.password.encode("utf-8"), salt).decode("utf8")
        return hashed_password


    def login(self) -> Tuple[str, str]:
        '''
        Retrieves JWT and club name.
        '''
        headers = {"content-type": "application/json"}
        url = "https://api.sorare.com/graphql"

        if bool(self.two_factor):
            try:
                query_factor = self.two_factor_query(url=url, headers=headers, ops_name='SignInMutation')
                query_response = json.loads(query_factor.content)

                errors = query_response.get("data",{}).get("signIn", {}).get("errors", [])

                if len(errors) and errors[0]['message'] != "2fa_missing":
                    raise LoginError(f"Please check email, password or two factor token - {errors[0]['message']}")

                self.opt_challenge = query_response.get("data",{}).get("signIn", {}).get("otpSessionChallenge", None)

                query_login = self.login_query(url=url, headers=headers, ops_name='SignInMutation')
                query_response = json.loads(query_login.content)

                jwt = query_response.get("data",{}).get("signIn", {}).get("currentUser", {}).get("jwtToken", {}).get("token", {})
                slug = query_response.get("data",{}).get("signIn", {}).get("currentUser", {}).get("slug", {})

                return jwt, slug

            except ValueError:
                raise LoginError("Please check email, password or two factor token")
        else:
            try:
                query = self.login_query(url=url, headers=headers, ops_name='SignInMutation')
                query_response = json.loads(query.content)
                errors = query_response.get("data",{}).get("signIn", {}).get("errors", [])
                if len(errors):
                    raise LoginError("Please check email, password or two factor token")
                else:
                    jwt = query_response.get("data",{}).get("signIn", {}).get("currentUser", {}).get("jwtToken", {}).get("token", {})
                    slug = query_response.get("data",{}).get("signIn", {}).get("currentUser", {}).get("slug", {})
                    return jwt, slug
            except ValueError:
                raise LoginError("Please check email, password or two factor token")