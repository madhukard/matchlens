"""Local-only MCP Apps bridge harness; not included in the deployment image.

Run the application on 8767, then this script; open http://127.0.0.1:8788.
This tests the bridge contract, not any vendor's actual client implementation.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen

PAGE = b"""<!doctype html><html><body style="margin:0">
<div id="status">Waiting for app initialization</div>
<iframe id="app" src="/widget" title="MatchLens embedded test"
style="width:100%;height:900px;border:0"></iframe>
<script>
const frame=document.getElementById('app');
const status=document.getElementById('status');
window.addEventListener('message',async event=>{
 if(event.source!==frame.contentWindow || event.data?.jsonrpc!=='2.0')return;
 const {id,method,params}=event.data;
 const reply=result=>frame.contentWindow.postMessage({jsonrpc:'2.0',id,result},'*');
 if(method==='ui/initialize'){
  status.textContent='Initialized MCP Apps bridge';
  reply({protocolVersion:'2026-01-26',hostInfo:{name:'test',version:'1'},
   hostCapabilities:{serverTools:{}},hostContext:{theme:'light'}});
 }else if(method==='tools/call'){
  const response=await fetch('/tools',{method:'POST',body:JSON.stringify(params)});
  reply(await response.json());
 }else if(method==='ui/update-model-context'){
  status.textContent='Model context: '+JSON.stringify(params.structuredContent);reply({});
 }else if(method==='ui/notifications/size-changed'){
  frame.style.height=Math.min(params.height,1800)+'px';
 }
});
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def send(self, body, content_type):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.send(PAGE, "text/html")
        elif self.path == "/widget":
            with urlopen("http://127.0.0.1:8767/") as response:
                self.send(response.read(), "text/html")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/tools":
            self.send_error(404)
            return
        size = min(int(self.headers.get("Content-Length", 0)), 10000)
        data = json.loads(self.rfile.read(size))
        request = Request(
            "http://127.0.0.1:8767/api/tools",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request) as response:
            self.send(response.read(), "application/json")


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8788), Handler).serve_forever()
