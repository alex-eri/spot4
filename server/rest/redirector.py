import logging
import signal
import functools
import asyncio
from aiohttp import web
import cachetools


sessions = cachetools.TTLCache(2048, 10)
success = "<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>\n"
success2 = '<HTML><HEAD><meta http-equiv="refresh" content="0; url={url}"><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>\n'
redirapple = """<HTML><HEAD>
<meta name="viewport" content="width=device-width, initial-scale=1">
<SCRIPT>
   window.setTimeout (function () {{
      var A = document.createElement ("a");
      A.setAttribute ("href", "{url}");
      var Body = document.getElementsByTagName ("body");
      if (Body.length > 0) {{
         Body = Body [0];
      }} else {{
         Body = document.createElement ("body");
         document.getElementsByTagName ("html") [0].appendChild (Body);
      }}
      Body.appendChild (A);
      A.click ();
   }}, 1000);
</SCRIPT>
<STYLE>
* {{
  font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, sans-serif;;
}}
html, body {{
  min-height: 100vh;
  min-height: -webkit-fill-available;
}}
a.button {{
  text-decoration: none;
  color: blue;
  line-height: 60px;
  letter-spacing: 2px;
  border: 1px solid blue;
  width: 180px;
  height: 60px;
  margin: 90px 20px;
  border-radius: 3px;
  display: block;
}}
h2 {{
  margin: 20px;
}}
</STYLE>
<TITLE>{msg}</TITLE></HEAD><BODY><center><h2>{msg}</h2>
<a href="{url}" class="button">{go}</a></center>
</BODY></HTML>
"""

strings = {
    'ru' : {'go': "Перейти", 'msg': "Необходимо продолжить авторизацию в браузере"},
    'kk' : {'go': "Ауысу", 'msg': "Авторизацияны браузерде жалғастыру қажет"},
    'en' : {'go': "Open", 'msg': "Open browser to complete authorization"},
    'uk-ua' : {'go': "Перейти", 'msg': "Необхідно продовжити авторизацію в браузері"}
}

async def stage1(request):
    query = request.query
    #key = (request.query.get('ip'), request.query.get('called'),request.query.get('mac'))
    key = request.remote
    session = sessions.setdefault(key, dict(query))
    ua = request.headers['User-Agent']
    l10n = request.headers.get('Accept-Language','en')
    if ({'mac', 'linklogin', 'called'}).issubset(set(query.keys())):
        redir_url = '/uam/?'+request.query_string
    else:
        redir_url = 'http://gstatic.com/generate_204'
    if 'CaptiveNetworkSupport' in ua or 'NetworkCTS' in ua:
        if session and session.get('ready'):
            session['ready'] = 2
            sessions[key] = session
            text = success
            return web.Response(text=text, content_type='text/html')
    if 'Mobile' in ua and not ('Safari' in ua or 'Firefox' in ua):
        if session.get('ready') == 2:
            text=success2.format(url=redir_url)
            return web.Response(text=text, content_type='text/html')
        session['ready'] = 1
        sessions[key] = session
        await asyncio.sleep(1)
        session = sessions.get(key)
        string = strings.get(l10n, strings['en'])
        text = redirapple.format(
            url=request.path_qs,
            **string
            )
        return web.Response(text=text, content_type='text/html')
    else:
        raise web.HTTPFound(redir_url)

async def main(port=8082):
    app = web.Application()
    app.stop = asyncio.Future()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, app.stop.cancel)
    app.add_routes([ web.get('/{tail:.*}', stage1), ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    await app.stop
