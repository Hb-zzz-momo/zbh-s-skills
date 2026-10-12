"""Bounded HTTPS transport; credentials never become request/audit artifacts."""
from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

from .engine import require


@dataclass(frozen=True)
class Configuration:
    endpoint: str = 'https://api.deepseek.com/chat/completions'
    model: str = 'deepseek-flash'
    api_key_env: str = 'DEEPSEEK_API_KEY'
    credential_file: str = ''
    timeout_seconds: int = 180
    max_retries: int = 2
    max_tokens: int = 16000
    max_images: int = 160
    thinking: str = 'disabled'
    simulation: bool = False
    scoring_policies: dict = field(default_factory=dict)
    review_policy: dict = field(default_factory=dict)

    def __post_init__(self):
        """A loopback test server is opt-in and can never masquerade as production."""
        url=urllib.parse.urlsplit(self.endpoint)
        local=url.hostname in ('127.0.0.1','localhost','::1')
        require(url.scheme=='https' or (self.simulation and local and url.scheme=='http'),'HTTPS required outside explicit loopback simulation')
        require(bool(url.hostname) and not url.username and not url.password and not url.query and not url.fragment,'invalid endpoint')
        require(not self.simulation or local,'simulation must use loopback')
        require(bool(re.fullmatch(r'[A-Za-z0-9._/-]+',self.model)),'invalid model name')
        require(type(self.simulation) is bool,'simulation must be boolean')
        require(type(self.timeout_seconds) is int and 1<=self.timeout_seconds<=600,'invalid timeout')
        require(type(self.max_retries) is int and 0<=self.max_retries<=3,'invalid retry limit')
        require(type(self.max_images) is int and 1<=self.max_images<=600,'invalid image limit')
        require(type(self.max_tokens) is int and 1<=self.max_tokens<=393216,'invalid token limit')
        require(self.thinking in ('enabled','disabled'),'invalid thinking mode')
        from .calibration import validate_policy
        require(isinstance(self.scoring_policies,dict),'评分政策必须按实验保存')
        for experiment,value in self.scoring_policies.items():validate_policy(value,experiment)
        from .recommendation import review_policy
        review_policy(self.review_policy)

    @classmethod
    def load(cls,path=None,credential_file=None):
        """Configuration carries a credential location, never the secret itself."""
        values=json.loads(Path(path).read_text('utf-8-sig')) if path else {}
        require(isinstance(values,dict),'configuration must be an object')
        if credential_file is not None: values['credential_file']=str(Path(credential_file).resolve())
        return cls(**values)

    def snapshot(self):
        return asdict(self)

    def credential(self):
        """Read a caller-authorized file only at send time; no environment scanning."""
        if self.simulation: return 'local-simulation-no-real-key'
        value=os.environ.get(self.api_key_env,'').strip()
        if not value and self.credential_file:
            raw=Path(self.credential_file).read_text('utf-8-sig').strip()
            if raw.startswith('{'):
                value=json.loads(raw).get('api_key','')
            else:
                candidates=re.findall(r'\bsk-[A-Za-z0-9_-]+',raw)
                require(len(candidates)==1,'credential file must contain exactly one API key')
                value=candidates[0]
        require(isinstance(value,str) and bool(value) and '\n' not in value and '\r' not in value,'API key missing/invalid; configure environment or credential file')
        return value


class TransportError(RuntimeError):
    def __init__(self,code,retryable=False):
        super().__init__(code)
        self.code=code
        self.retryable=retryable


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        # Never forward an Authorization header to a redirected origin.
        return None


class DeepSeekClient:
    def __init__(self,configuration):
        self.configuration=configuration

    def complete(self,payload,on_attempt=lambda record:None):
        """Retry transient transport errors only; return no synthetic score on failure.

        A timeout may already have incurred provider usage. Retries are separate
        attempts recorded for audit, not claimed as exactly-once external calls.
        """
        config=self.configuration
        require(payload.get('model')==config.model,'request/config model mismatch')
        key=config.credential()
        body=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode('utf-8')
        require(len(body)<=45*1024*1024,'request exceeds conservative 45 MiB limit')
        opener=urllib.request.build_opener(_NoRedirect())
        for number in range(config.max_retries+1):
            started=time.monotonic()
            record={'attempt_number':number+1,'request_sha256':hashlib.sha256(body).hexdigest(),
                    'request_bytes':len(body),'model_requested':config.model,'simulation':config.simulation}
            error=None
            try:
                req=urllib.request.Request(config.endpoint,data=body,headers={'Content-Type':'application/json','Authorization':'Bearer '+key},method='POST')
                with opener.open(req,timeout=config.timeout_seconds) as response:
                    data=response.read(16*1024*1024+1)
                    require(len(data)<=16*1024*1024,'provider response exceeds limit')
                    decoded=json.loads(data.decode('utf-8'))
                    require(isinstance(decoded,dict),'provider response must be object')
                    record.update(http_status=response.status,response_sha256=hashlib.sha256(data).hexdigest(),
                                  response_id=decoded.get('id'),model_returned=decoded.get('model'),
                                  system_fingerprint=decoded.get('system_fingerprint'),usage=decoded.get('usage'),
                                  elapsed_seconds=round(time.monotonic()-started,3))
                    # Visible result is enough for replay; do not persist hidden reasoning.
                    visible=json.loads(json.dumps(decoded))
                    for choice in visible.get('choices',[]):
                        choice.get('message',{}).pop('reasoning_content',None)
                    record['visible_response']=visible
                    on_attempt(record)
                    return decoded
            except urllib.error.HTTPError as exc:
                error=TransportError('http_'+str(exc.code),exc.code in (408,429,500,502,503,504))
                record['http_status']=exc.code
                exc.close()
            except (urllib.error.URLError,socket.timeout,TimeoutError,ConnectionError):
                error=TransportError('network_or_timeout',True)
            except (UnicodeError,ValueError):
                error=TransportError('invalid_provider_response',False)
            record.update(error=error.code,elapsed_seconds=round(time.monotonic()-started,3))
            on_attempt(record)
            if not error.retryable or number==config.max_retries: raise error
            time.sleep(min(2**number,8))
