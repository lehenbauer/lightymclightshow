#!/usr/bin/env python3
import argparse, asyncio, json, os, struct, sys

def pack(obj: dict) -> bytes:
    b = json.dumps(obj, separators=(",", ":")).encode()
    return struct.pack(">I", len(b)) + b

async def read_frame(reader: asyncio.StreamReader) -> dict:
    hdr = await reader.readexactly(4)
    (n,) = struct.unpack(">I", hdr)
    data = await reader.readexactly(n)
    return json.loads(data)

async def open_conn(socket_path: str | None, tcp: str | None):
    if socket_path:
        return await asyncio.open_unix_connection(socket_path)
    assert tcp, "either --socket or --tcp required"
    host, port = tcp.rsplit(":", 1)
    return await asyncio.open_connection(host, int(port))

async def rpc_once(sock: str | None, tcp: str | None, method: str, params: dict | None = None):
    reader, writer = await open_conn(sock, tcp)
    msg = {"id": 1, "method": method, "params": params or {}}
    writer.write(pack(msg)); await writer.drain()
    try:
        # Add 5 second timeout for daemon response
        resp = await asyncio.wait_for(read_frame(reader), timeout=5.0)
    except asyncio.TimeoutError:
        writer.close(); await writer.wait_closed()
        raise SystemExit(f"error: daemon did not respond within 5 seconds (may be busy processing)")
    writer.close(); await writer.wait_closed()
    if not resp.get("ok", False):
        raise SystemExit(f"error: {resp.get('error')}")
    return resp.get("result")

async def watch(sock: str | None, tcp: str | None):
    reader, writer = await open_conn(sock, tcp)
    writer.write(pack({"id": 1, "method": "subscribe", "params": {}})); await writer.drain()
    # print the ack
    _ = await read_frame(reader)
    print("subscribed; waiting for status events (Ctrl+C to exit)")
    try:
        while True:
            evt = await read_frame(reader)
            print(json.dumps(evt, indent=2))
    finally:
        writer.close(); await writer.wait_closed()

def parse_params(kvs: list[str]) -> dict:
    out = {}
    for kv in kvs:
        if "=" not in kv:
            raise SystemExit(f"bad param '{kv}', expected key=value")
        k, v = kv.split("=", 1)
        # try JSON parse (so true/false, numbers, arrays work); else raw string
        try:
            out[k] = json.loads(v)
        except json.JSONDecodeError:
            out[k] = v
    return out

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--socket", help="Unix socket path, e.g. /tmp/lightymc.sock")
    ap.add_argument("--tcp", help="TCP host:port, e.g. 127.0.0.1:8765")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list available effects")

    p_start = sub.add_parser("start", help="start an effect by name")
    p_start.add_argument("name")
    p_start.add_argument("param", nargs="*", help="key=value JSON-ish (e.g., strip=\"circular\" speed=0.7)")

    p_preset = sub.add_parser("preset", help="run a preset by name (if supported)")
    p_preset.add_argument("name")

    sub.add_parser("stop-all", help="stop all effects")

    sub.add_parser("blackout", help="stop all effects and blackout all strips")

    sub.add_parser("watch", help="subscribe to status stream")

    args = ap.parse_args()
    if not args.socket and not args.tcp:
        ap.error("Provide --socket or --tcp")
    try:
        if args.cmd == "list":
            r = await rpc_once(args.socket, args.tcp, "list_effects")
            print("\n".join(r["effects"]))
        elif args.cmd == "start":
            params = {"name": args.name, "params": parse_params(args.param)}
            r = await rpc_once(args.socket, args.tcp, "start_effect", params)
            print(r)
        elif args.cmd == "preset":
            r = await rpc_once(args.socket, args.tcp, "run_preset", {"name": args.name})
            print(r)
        elif args.cmd == "stop-all":
            r = await rpc_once(args.socket, args.tcp, "stop_all")
            print(r)
        elif args.cmd == "blackout":
            r = await rpc_once(args.socket, args.tcp, "blackout")
            print(r)
        elif args.cmd == "watch":
            await watch(args.socket, args.tcp)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    asyncio.run(main())

