#!/usr/bin/env python3
"""Lokal webserver for Zak McKracken HD i nettleseren.

Lytter bare på 127.0.0.1, så siden kan bare åpnes fra maskinen selv. Spillet og HD-grafikken
tilhører Lucasfilm/Disney og skal aldri legges på en åpen adresse: ingen GitHub Pages, ingen
publisering, ingen opplasting. Adressen er derfor låst her og kan ikke endres med et valg.

Bruk: engine/web/server.py [--port 8000] MAPPE
"""

import argparse
import functools
import http.server
import sys

HOST = "127.0.0.1"  # bare denne maskinen, aldri 0.0.0.0
LOKALE_NAVN = {"localhost", "127.0.0.1"}


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".js": "text/javascript",
        ".json": "application/json",
    }

    def _lokal(self) -> bool:
        # Godtar bare forespørsler til localhost, så en annen nettside ikke kan lese filene
        # gjennom et navn som peker hit (DNS rebinding).
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        return host in LOKALE_NAVN

    def do_GET(self):
        if not self._lokal():
            self.send_error(403, "Bare localhost")
            return
        super().do_GET()

    def do_HEAD(self):
        if not self._lokal():
            self.send_error(403, "Bare localhost")
            return
        super().do_HEAD()

    def end_headers(self):
        # Moddene og spillfilene kan byttes mellom to starter. Nettleseren spør da alltid
        # om filen er endret, i stedet for å bruke en gammel kopi.
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_request(self, code="-", size="-"):
        # Bare feil i terminalen; spillet henter hundrevis av filer.
        try:
            feil = int(code) >= 400
        except (TypeError, ValueError):
            feil = False
        if feil:
            super().log_request(code, size)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("mappe")
    a = p.parse_args()

    handler = functools.partial(Handler, directory=a.mappe)
    try:
        server = http.server.ThreadingHTTPServer((HOST, a.port), handler)
    except OSError as e:
        print(f"Kunne ikke starte webserveren på {HOST}:{a.port}: {e}", file=sys.stderr)
        print("Er porten i bruk? Velg en annen med --port.", file=sys.stderr)
        return 1
    print(f"Webserveren lytter på {HOST}:{a.port}, bare på denne maskinen. Ctrl+C stopper den.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
