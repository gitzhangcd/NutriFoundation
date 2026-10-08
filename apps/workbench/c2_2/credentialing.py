"""OIDC token verification primitive, NOT a real provider deployment.

Only trusted server configuration may select keys/issuer/audience. Verified
identity does not confer qualification, slot assignment or consent.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any
import jwt

class CredentialError(ValueError):pass

@dataclass(frozen=True)
class OIDCPolicy:
    issuer:str
    audience:str
    keys:dict[str,Any]
    require_mfa:bool=True

    def verify(self,id_token:str,*,expected_nonce:str)->dict:
        if not expected_nonce or len(expected_nonce)<12:raise CredentialError('EXPECTED_NONCE_REQUIRED')
        try:
            header=jwt.get_unverified_header(id_token)
            if header.get('alg')!='RS256' or not header.get('kid'):
                raise CredentialError('JWT_ALGORITHM_OR_KID_REJECTED')
            key=self.keys.get(header['kid'])
            if not key:raise CredentialError('UNKNOWN_IDP_SIGNING_KEY')
            claims=jwt.decode(id_token,key=key,algorithms=['RS256'],issuer=self.issuer,
                audience=self.audience,options={'require':['exp','iat','iss','aud','sub','nonce']},leeway=0)
            if claims.get('nonce')!=expected_nonce:raise CredentialError('NONCE_MISMATCH')
            if not isinstance(claims['sub'],str) or not claims['sub'].strip():raise CredentialError('EMPTY_SUBJECT')
            if self.require_mfa and not (set(claims.get('amr',[])) & {'mfa','otp','hwk'}):
                raise CredentialError('MFA_REQUIRED')
            return {'subject':claims['sub'],'issuer':claims['iss'],'audience':self.audience,
                    'authenticated':True,'mfa_verified':self.require_mfa,'identity_only':True}
        except CredentialError:raise
        except (jwt.PyJWTError,TypeError,KeyError,ValueError) as ex:
            raise CredentialError('TOKEN_REJECTED') from ex

def credential_prerequisites(config:dict)->list[str]:
    blockers=[]
    if not config.get('idp_configured_with_trusted_jwks'):blockers.append('TRUSTED_IDP_NOT_CONFIGURED')
    if not config.get('license_checked_by_independent_registrar'):blockers.append('EXPERT_QUALIFICATION_NOT_VERIFIED')
    if not config.get('case_prior_exposure_screen_signed'):blockers.append('PRIOR_EXPOSURE_SCREEN_PENDING')
    if not config.get('real_expert_consent_recorded'):blockers.append('CONSENT_RECORD_PENDING')
    if not config.get('same_case_cross_arm_assignment_atomic'):blockers.append('REAL_IDENTITY_CROSS_ARM_GATE_UNVERIFIED')
    return blockers
