from mangum import Mangum
from axonai_api import app
handler = Mangum(app, lifespan="off")
