#!/usr/bin/env python3
"""Dev Crew — дверной клиент (отправить сообщение агенту через его webhook-дверь).

Подписывает запрос HMAC-SHA256 (заголовок X-Hub-Signature-256) и POST-ит
сообщение в /webhooks/inbox выбранного агента. Ответ агент обрабатывает
асинхронно (результат — в его логах или delivery-таргете), клиент лишь
подтверждает приём (202).

Использование:
  # с хоста (менеджер/человек)
  python3 crew-send.py developer "сделай задачу"

  # из контейнера (агент -> агент): используем container_url
  python3 crew-send.py qa "просьба от developer" --container

Ноль зависимостей (только stdlib) — работает в любом окружении.
"""
import sys
import os
import json
import hmac
import hashlib
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "agents.json")


def load_registry(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sign(secret: str, payload: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def send(agent: str, message: str, use_container: bool = False) -> tuple[int, str]:
    registry = load_registry(REGISTRY)
    if agent not in registry:
        sys.exit(f"Неизвестный агент '{agent}'. Доступно: {', '.join(registry)}")

    cfg = registry[agent]
    url = cfg["container_url"] if use_container else cfg["host_url"]
    secret = cfg["secret"]

    payload = json.dumps({"message": message}, ensure_ascii=False)
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sign(secret, payload),
    }
    req = urllib.request.Request(url, data=payload.encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, resp.read().decode("utf-8")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    use_container = "--container" in sys.argv
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    agent, message = args[0], args[1]
    try:
        status, body = send(agent, message, use_container)
    except urllib.error.HTTPError as e:
        print(f"[{agent}] HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"[{agent}] error: {e}")
        sys.exit(1)
    print(f"[{agent}] {status}: {body}")


if __name__ == "__main__":
    main()
