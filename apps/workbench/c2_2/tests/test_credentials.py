import time
import pytest
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from credentialing import OIDCPolicy,CredentialError,credential_prerequisites

@pytest.fixture
def signed():
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    pub=key.public_key(); policy=OIDCPolicy(issuer='https://idp.test.invalid',audience='wb-synthetic',keys={'T1':pub})
    claims={'iss':policy.issuer,'aud':policy.audience,'sub':'SYN-0001','iat':int(time.time()),'exp':int(time.time())+600,
            'nonce':'1234567890-A-test','amr':['pwd','mfa']}
    return key,policy,claims

def encode(key,claims,alg='RS256'):
    return jwt.encode(claims,key,algorithm=alg,headers={'kid':'T1'})

def test_valid_identity_does_not_qualify_expert(signed):
    key,policy,c=signed; x=policy.verify(encode(key,c),expected_nonce=c['nonce'])
    assert x['authenticated'] and x['identity_only'] and 'qualification' not in x

def test_wrong_nonce(signed):
    key,p,c=signed
    with pytest.raises(CredentialError,match='NONCE'):p.verify(encode(key,c),expected_nonce='wrong-nonce-123456')

def test_wrong_audience(signed):
    key,p,c=signed;c['aud']='elsewhere'
    with pytest.raises(CredentialError,match='TOKEN_REJECTED'):p.verify(encode(key,c),expected_nonce=c['nonce'])

def test_expired_token(signed):
    key,p,c=signed;c['exp']=int(time.time())-1
    with pytest.raises(CredentialError,match='TOKEN_REJECTED'):p.verify(encode(key,c),expected_nonce=c['nonce'])

def test_unsigned_token(signed):
    key,p,c=signed;t=jwt.encode(c,key='',algorithm='none',headers={'kid':'T1'})
    with pytest.raises(CredentialError,match='JWT_ALGORITHM'):p.verify(t,expected_nonce=c['nonce'])

def test_unknown_key(signed):
    key,p,c=signed;t=jwt.encode(c,key,algorithm='RS256',headers={'kid':'OTHER'})
    with pytest.raises(CredentialError,match='UNKNOWN_IDP'):p.verify(t,expected_nonce=c['nonce'])

def test_mfa_missing(signed):
    key,p,c=signed;c['amr']=['pwd']
    with pytest.raises(CredentialError,match='MFA'):p.verify(encode(key,c),expected_nonce=c['nonce'])

def test_missing_exp(signed):
    key,p,c=signed;del c['exp']
    with pytest.raises(CredentialError,match='TOKEN_REJECTED'):p.verify(encode(key,c),expected_nonce=c['nonce'])

def test_credentials_not_self_attestation():
    assert len(credential_prerequisites({}))==5
    assert 'TRUSTED_IDP_NOT_CONFIGURED' in credential_prerequisites({'idp_configured_with_trusted_jwks':False})
