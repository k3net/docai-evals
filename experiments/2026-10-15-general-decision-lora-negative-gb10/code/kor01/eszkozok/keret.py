"""01-es kör — a döntési kérdés keretszövege (01-runbook 2. pont), a 00-ás `common.render_user` mintájára.

A keretszöveg az item nyelvét követi (hu / en); az eszközleírások a forrás nyelvén maradnak. A kimenet egyetlen
címketoken: `A`…`J` vagy `X`. A leírás hossza korlátozható (`desc_max` karakter), mert a tréning max_len-je véges.
"""

from __future__ import annotations

LABELS = list("ABCDEFGHIJ")
NONE_LABEL = "X"

FRAME = {
    "hu": {"system": "Döntési modell vagy. Egyetlen betűvel válaszolj: a választott opció betűjével.",
           "task": "Feladat: melyik eszközt kell meghívni a felhasználó kérésére?",
           "request": "Kérés", "context": "Előzmény", "options": "Opciók:", "required": "kötelező", "none": "Egyik sem"},
    "en": {"system": "You are a decision model. Answer with a single letter: the letter of the chosen option.",
           "task": "Task: which tool should be called for the user's request?",
           "request": "Request", "context": "Context", "options": "Options:", "required": "required", "none": "None of these"},
}


def clip(text: str, n: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def render_user(item: dict, order: list[str | None], desc_max: int = 300, hist_max: int = 300) -> str:
    f = FRAME[item.get("lang", "en")]
    opts = {o["id"]: o for o in item["options"]}
    lines = [f["task"]]
    hist = [m.get("content") or "" for m in item.get("history") or [] if (m.get("content") or "").strip()]
    if hist:
        lines.append(f"{f['context']}: {clip(' / '.join(hist), hist_max)}")
    lines += [f"{f['request']}: \"{clip(item['request'], 1000)}\"", f["options"]]
    labs = iter(LABELS)
    for oid in order:
        if oid is None:
            lines.append(f"{NONE_LABEL}) {f['none']}")
            continue
        o = opts[oid]
        req = f" ({f['required']}: {', '.join(o['required'])})" if o.get("required") else ""
        lines.append(f"{next(labs)}) {o['name']}: {clip(o['description'], desc_max)}{req}")
    return "\n".join(lines)


def messages_for(item: dict, order: list[str | None], **kw) -> list[dict]:
    return [{"role": "system", "content": FRAME[item.get("lang", "en")]["system"]},
            {"role": "user", "content": render_user(item, order, **kw)}]
