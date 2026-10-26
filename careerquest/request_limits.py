"""Bound JSON request size, including chunked requests without Content-Length."""
from starlette.responses import JSONResponse


class BodyLimit:
    def __init__(self,app,maximum=65536):self.app,self.maximum=app,maximum
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope['method'] in ('GET','HEAD','OPTIONS'):
            return await self.app(scope,receive,send)
        chunks=[];size=0
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            body=message.get('body',b'');size+=len(body)
            if size>self.maximum:
                response=JSONResponse({'detail':'Request is too large'},status_code=413)
                return await response(scope,receive,send)
            chunks.append(body)
            if not message.get('more_body',False):break
        consumed=False
        async def bounded_receive():
            nonlocal consumed
            if not consumed:
                consumed=True
                return {'type':'http.request','body':b''.join(chunks),'more_body':False}
            return await receive()
        return await self.app(scope,bounded_receive,send)
