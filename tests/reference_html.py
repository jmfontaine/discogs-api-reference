"""Build HTML with the layout of discogs.com/developers."""

from __future__ import annotations


def cf_email(address: str, key: int = 0x42) -> str:
    """Encode *address* the way Cloudflare obfuscates emails."""
    return f"{key:02x}" + "".join(f"{ord(char) ^ key:02x}" for char in address)


def page(slug: str, title: str, body: str = "") -> str:
    return (
        f'<div class="page-section" data-page="{slug}">'
        '<div class="panel panel-default"><div class="panel-heading">'
        f'<h1 id="{slug}" class="panel-heading-title"> {title}\n</h1></div>'
        f"{body}</div></div>"
    )


ENDPOINT = """
<h2 id="database-thing"> Thing</h2>
<section class="panel panel-info" id="database-thing-get">
  <div class="panel-heading">
    <div class="pull-right"><span class="sr-only-action-name">Get Thing</span></div>
    <div class="pull-left"><a class="btn btn-xs btn-primary"
      href="#page:database,header:database-thing-get">GET</a></div>
    <div class="overflow-hidden"><code>/things/{thing_id}</code></div>
  </div>
  <div class="panel-body"><p>Get a thing</p></div>
  <ul class="list-group">
    <li class="list-group-item"><strong> Response
  \n<code>200</code> </strong>
      <button class="toggle-button" type="button">Toggle</button></li>
    <li class="list-group-item"><h5>Body</h5><pre><code>{
    "id": 1
}</code></pre></li>
  </ul>
</section>
"""


def reference_html(*pages: str) -> str:
    """A minimal page with the layout of discogs.com/developers."""
    return (
        '<html><body><nav><a href="#page:home">Home</a></nav>'
        '<div class="row"><div class="col-md-9">'
        + "".join(pages)
        + "</div></div></body></html>"
    )
