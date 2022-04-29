import falcon
import falcon.asgi

class PublishResource:
    async def on_get(self, req, resp):
        resp.data = {
            "hallo": "welt"
        }

app = falcon.asgi.App()
app.add_route("/api/packages/versions/new", PublishResource())
