const LAMBDA_URL = 'https://73edpnyeqs6gl3eh4gyfnwoji40ldhgo.lambda-url.ap-southeast-2.on.aws';

export default async function handler(req, res) {
  // Strip /api prefix to get the real path
  const path = req.url.replace(/^\/api/, '') || '/';
  const targetUrl = `${LAMBDA_URL}${path}`;

  try {
    const fetchOptions = {
      method: req.method,
      headers: { 'Content-Type': 'application/json' },
    };

    if (req.method !== 'GET' && req.method !== 'HEAD' && req.body) {
      fetchOptions.body = JSON.stringify(req.body);
    }

    const response = await fetch(targetUrl);
    const data = await response.json();

    // Set CORS headers ourselves (clean, single value)
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    res.status(response.status).json(data);
  } catch (err) {
    console.error('Proxy error:', err);
    res.status(502).json({ error: 'Failed to reach API', details: err.message });
  }
}
