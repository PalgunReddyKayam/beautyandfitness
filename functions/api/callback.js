// Step 2: GitHub sends the user back here; exchange the code for a token and hand it to Decap.
export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const cookie = request.headers.get("Cookie") || "";
  const saved = (cookie.match(/oauth_state=([^;]+)/) || [])[1];

  let status = "error";
  let payload = { error: "Login failed. Try again." };

  if (code && state && saved === state) {
    const res = await fetch("https://github.com/login/oauth/access_token", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json", "User-Agent": "decap-cms-oauth" },
      body: JSON.stringify({ client_id: env.GITHUB_CLIENT_ID, client_secret: env.GITHUB_CLIENT_SECRET, code }),
    });
    const data = await res.json();
    if (data.access_token) {
      status = "success";
      payload = { token: data.access_token, provider: "github" };
    } else {
      payload = { error: data.error_description || "GitHub did not return a token." };
    }
  }

  const html = `<!doctype html><html><body><script>
(function () {
  function send() {
    window.opener.postMessage(
      "authorization:github:${status}:" + JSON.stringify(${JSON.stringify(payload)}),
      "*"
    );
  }
  window.addEventListener("message", function (e) {
    if (typeof e.data === "string" && e.data.indexOf("authorizing:github") === 0) send();
  }, false);
  window.opener.postMessage("authorizing:github", "*");
})();
</script><p>Logging you in…</p></body></html>`;

  return new Response(html, {
    status: 200,
    headers: { "Content-Type": "text/html", "Set-Cookie": "oauth_state=; Path=/; Max-Age=0" },
  });
}
