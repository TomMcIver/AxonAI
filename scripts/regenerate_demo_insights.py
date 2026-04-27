#!/usr/bin/env python3
"""Regenerate teacher insights for demo students via live Lambda endpoint."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request


LAMBDA_BASE_URL = "https://73edpnyeqs6gl3eh4gyfnwoji40ldhgo.lambda-url.ap-southeast-2.on.aws"
DEMO_STUDENT_IDS = [
    1, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563, 564,
    565, 566, 567, 568, 569, 570, 571,
]


def call_generate(student_id: int) -> tuple[bool, str]:
    url = f"{LAMBDA_BASE_URL}/student/{student_id}/generate-insights"
    req = urllib.request.Request(url=url, data=b"{}", method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            body = response.read().decode("utf-8")
            _ = json.loads(body) if body else {}
            return True, f"status={response.status}"
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        return False, f"status={err.code} body={body}"
    except Exception as err:  # noqa: BLE001
        return False, f"error={err}"


def main() -> None:
    success = 0
    failed_ids: list[int] = []

    for student_id in DEMO_STUDENT_IDS:
        ok, info = call_generate(student_id)
        if ok:
            success += 1
            print(f"[OK] student_id={student_id} {info}")
        else:
            failed_ids.append(student_id)
            print(f"[FAIL] student_id={student_id} {info}")
        time.sleep(2)

    print("")
    print(f"Total success count: {success}/{len(DEMO_STUDENT_IDS)}")
    print(f"Failed IDs: {failed_ids if failed_ids else 'None'}")


if __name__ == "__main__":
    main()

