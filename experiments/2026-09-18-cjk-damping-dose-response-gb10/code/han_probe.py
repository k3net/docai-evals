#!/usr/bin/env python3
"""Save complete vLLM chat requests/responses and detect Han in final content.
No production writes, no automatic server restarts. Python standard library only.

Round5 changes (see 01-qwen36-nyelvkeveres-runbook.md):
  * --sampling {original,cron,cron-nopenalty,chat,greedy}: the profiles are read from
    the application source, so an arm is self-describing; cron-nopenalty isolates
    presence_penalty/repetition_penalty, which the cron path sets aggressively.
  * --no-instrument: send the request untouched (no logprobs/token ids), to prove the
    phenomenon is not an artefact of the instrumentation itself.
  * --seed: recorded and sent, so stochastic arms are repeatable.
  * other-script detection (kana, hangul, fullwidth, CJK punctuation) reported
    separately from Han, without changing final_han semantics.
  * expected_prompt_tokens per case: verifies a replayed prompt is actually faithful.
"""
import argparse, copy, hashlib, json, os, time, unicodedata, uuid
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


# What the CRON path actually sends (src/cron/runner.py, the code state of the run under
# investigation). Read from the source, not assumed: temperature 0.6 / top_p 0.95 /
# presence_penalty 1.5 as named arguments, and top_k 20 / min_p 0 /
# repetition_penalty 1.05 through extra_body. The 0.1 in config.py belongs to a
# different call path and never reaches this request.
CRON_SAMPLING = {'temperature': 0.6, 'top_p': 0.95, 'top_k': 20, 'min_p': 0,
                 'presence_penalty': 1.5, 'repetition_penalty': 1.05}
# Same request with both penalties neutralised — isolates the penalty terms, which are
# the strongest single candidate for pushing probability mass off already-used
# (Hungarian) tokens and onto unused ones.
CRON_NO_PENALTY_SAMPLING = dict(CRON_SAMPLING, presence_penalty=0, repetition_penalty=1.0)
# The chat path's profile, for contrast only.
CHAT_SAMPLING = {'temperature': 0.1, 'top_p': 0.95, 'top_k': 20, 'min_p': 0,
                 'presence_penalty': 0, 'repetition_penalty': 1.0}
GREEDY_SAMPLING = {'temperature': 0, 'top_p': 1, 'top_k': -1, 'min_p': 0,
                   'presence_penalty': 0, 'repetition_penalty': 1.0}
SAMPLING_PROFILES = {'cron': CRON_SAMPLING, 'cron-nopenalty': CRON_NO_PENALTY_SAMPLING,
                     'chat': CHAT_SAMPLING, 'greedy': GREEDY_SAMPLING}

# Scripts that are not Han but still signal language mixing in a Hungarian answer.
OTHER_SCRIPT_RANGES = (
    (0x1100, 0x11FF),  # hangul jamo
    (0x3000, 0x303F),  # CJK symbols and punctuation
    (0x3040, 0x309F),  # hiragana
    (0x30A0, 0x30FF),  # katakana
    (0xAC00, 0xD7AF),  # hangul syllables
    (0xFF00, 0xFFEF),  # halfwidth and fullwidth forms
)


def _spans(text, predicate):
    if not isinstance(text, str):
        return []
    spans, start = [], None
    for i, ch in enumerate(text + ' '):
        hit = predicate(ch)
        if hit and start is None:
            start = i
        if not hit and start is not None:
            spans.append({'start': start, 'end': i, 'text': text[start:i],
                          'context': text[max(0, start-60):min(len(text), i+60)]})
            start = None
    return spans


def _is_han(ch):
    return unicodedata.name(ch, '').startswith(
        ('CJK UNIFIED IDEOGRAPH-', 'CJK COMPATIBILITY IDEOGRAPH-'))


def _is_other_script(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in OTHER_SCRIPT_RANGES)


def han_spans(text):
    """Han ideographs only. Recognises a script, not a language: Japanese kanji hits too."""
    return _spans(text, _is_han)


def other_script_spans(text):
    """Kana, hangul, fullwidth forms and CJK punctuation. Reported separately from Han."""
    return _spans(text, _is_other_script)


def sha(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def stats(body, expected_prompt_tokens=None):
    choice = body['choices'][0]
    msg = choice['message']
    content = msg.get('content')
    reasoning = msg.get('reasoning') or msg.get('reasoning_content')
    lp = (choice.get('logprobs') or {}).get('content') or []
    ordered, canonical = [], []
    for entry in lp:
        pairs = [(x['token'], x['logprob']) for x in entry.get('top_logprobs', [])]
        ordered.append(pairs)
        canonical.append(sorted(pairs, key=lambda x: x[0]))
    detail = (body.get('usage') or {}).get('prompt_tokens_details') or {}
    prompt_tokens = (body.get('usage') or {}).get('prompt_tokens')
    out = {'has_final_content': isinstance(content, str) and bool(content),
           'final_han': han_spans(content), 'reasoning_han': han_spans(reasoning),
           'final_other_script': other_script_spans(content),
           'reasoning_other_script': other_script_spans(reasoning),
           'final_chars': len(content) if isinstance(content, str) else None,
           'ordered_top_hash': sha(ordered) if lp else None,
           'canonical_top_hash': sha(canonical) if lp else None,
           'cached_tokens': detail.get('cached_tokens'),
           'prompt_tokens': prompt_tokens,
           'completion_tokens': (body.get('usage') or {}).get('completion_tokens'),
           'finish_reason': choice.get('finish_reason'),
           'has_prompt_token_ids': isinstance(body.get('prompt_token_ids'), list),
           'has_output_token_ids': isinstance(choice.get('token_ids'), list),
           'content_sha256': sha(content)}
    if expected_prompt_tokens is not None:
        out['expected_prompt_tokens'] = expected_prompt_tokens
        out['prompt_tokens_delta'] = (
            None if prompt_tokens is None else prompt_tokens - expected_prompt_tokens)
        out['prompt_faithful'] = (out['prompt_tokens_delta'] == 0)
    return out


def call(base, payload):
    headers = {'Content-Type': 'application/json'}
    key = os.environ.get('VLLM_API_KEY')
    if key:
        headers['Authorization'] = 'Bearer ' + key
    req = Request(base.rstrip('/') + '/v1/chat/completions',
                  data=json.dumps(payload, ensure_ascii=False).encode(), headers=headers)
    with urlopen(req, timeout=1800) as resp:
        return json.load(resp)


def parse_overrides(pairs):
    """--set key=value párok tipizálva. Egy kar így pontosan egy tengelyen mozdítható
    el a valódi profiltól, anélkül hogy új nevesített profilt kellene bevezetni."""
    out = {}
    for item in pairs or ():
        if '=' not in item:
            raise ValueError(f'--set kulcs=érték alakot vár: {item!r}')
        k, v = item.split('=', 1)
        try:
            out[k.strip()] = json.loads(v)
        except json.JSONDecodeError:
            out[k.strip()] = v
    return out


def prepare(original, salt, sampling='original', instrument=True, seed=None, overrides=None):
    p = copy.deepcopy(original)
    if not isinstance(p.get('messages'), list) or not p.get('model'):
        raise ValueError('Each request needs model and messages.')
    if 'max_tokens' not in p and 'max_completion_tokens' not in p:
        raise ValueError('Record the actual generation token limit in each request.')
    if p.get('n', 1) != 1:
        raise ValueError('This diagnostic requires n=1; record a separate n=1 case.')
    p.update(stream=False, cache_salt=salt)
    p.pop('stream_options', None)
    if instrument:
        p.update(logprobs=True, top_logprobs=20,
                 return_tokens_as_token_ids=True, return_token_ids=True)
    else:
        # Uninstrumented control: the phenomenon must survive without the extra fields.
        for k in ('logprobs', 'top_logprobs', 'return_tokens_as_token_ids',
                  'return_token_ids'):
            p.pop(k, None)
    if sampling in SAMPLING_PROFILES:
        p.update(SAMPLING_PROFILES[sampling])
    elif sampling != 'original':
        raise ValueError(f'Unknown sampling profile: {sampling}')
    if overrides:
        p.update(overrides)
    if seed is not None:
        p['seed'] = seed
    return p


def effective_sampling(payload):
    """What this request actually pins. Anything absent is decided by the server's
    generation_config defaults, which is exactly the trap this field documents."""
    return {k: payload.get(k, '<server default>')
            for k in ('temperature', 'top_p', 'top_k', 'min_p', 'presence_penalty',
                      'repetition_penalty', 'frequency_penalty', 'seed')}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', required=True)
    ap.add_argument('--cases', type=Path, required=True)
    ap.add_argument('--case-id')
    ap.add_argument('--arm', required=True)
    ap.add_argument('--mode', choices=['fresh', 'self', 'cross'], required=True)
    ap.add_argument('--repeat', type=int, default=3)
    ap.add_argument('--sampling', default='original',
                    choices=['original'] + sorted(SAMPLING_PROFILES),
                    help='original: exactly as recorded in the case; cron: the real '
                         'cron profile (0.6/0.95/20 + pp 1.5 + rp 1.05); '
                         'cron-nopenalty: the same with both penalties off; '
                         'chat: the chat path (0.1/0.95/20); greedy: 0/1/-1, no penalties')
    ap.add_argument('--greedy', action='store_true',
                    help='deprecated alias for --sampling greedy')
    ap.add_argument('--no-instrument', action='store_true',
                    help='send the request without logprobs/token-id fields')
    ap.add_argument('--seed', type=int)
    ap.add_argument('--set', action='append', metavar='KULCS=ÉRTÉK', default=[],
                    help='egyedi mintavételezési felülírás a profil UTÁN alkalmazva, '
                         'pl. --set presence_penalty=0 --set temperature=0.3')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    if a.repeat < 1:
        ap.error('--repeat must be positive')
    sampling = 'greedy' if a.greedy else a.sampling
    overrides = parse_overrides(a.set)
    instrument = not a.no_instrument
    cases = [json.loads(s) for s in a.cases.read_text().splitlines() if s.strip()]
    if a.case_id:
        cases = [c for c in cases if c['id'] == a.case_id]
    if not cases:
        ap.error('No matching cases')
    a.out.mkdir(parents=True, exist_ok=False)
    run = uuid.uuid4().hex
    rows = []
    for ci, case in enumerate(cases):
        if a.mode == 'cross' and 'warmup_request' not in case:
            raise ValueError(f'{case["id"]}: cross mode needs original warmup_request')
        expected = case.get('expected_prompt_tokens')
        shared_salt = f'han-{run}-{ci}'
        sequence = ([('warmup', case['warmup_request'])] if a.mode == 'cross' else [])
        sequence += [(f'target-{i+1}', case['request']) for i in range(a.repeat)]
        for si, (role, original) in enumerate(sequence):
            salt = f'{shared_salt}-{si}' if a.mode == 'fresh' else shared_salt
            payload = prepare(original, salt, sampling, instrument, a.seed, overrides)
            record = {'arm': a.arm, 'mode': a.mode, 'case_id': case['id'], 'role': role,
                      'sampling_profile': sampling, 'instrumented': instrument,
                      'effective_sampling': effective_sampling(payload),
                      'request': payload, 'request_hash': sha(payload), 'time': time.time()}
            dest = a.out / f'{ci:03d}-{si:03d}.json'
            t0 = time.monotonic()
            try:
                body = call(a.url, payload)
                record['response'] = body
                record['stats'] = stats(body, expected if role.startswith('target') else None)
                record['seconds'] = time.monotonic() - t0
                cached = record['stats']['cached_tokens']
                record['cache_observation'] = ('unknown' if cached is None else
                                               'hit' if cached > 0 else 'miss')
                if a.mode == 'fresh' and cached is not None and cached > 0:
                    raise RuntimeError('Fresh salt still reports cache hits; invalidate this arm.')
            except Exception as exc:
                record['error'] = str(exc)
                if isinstance(exc, HTTPError):
                    record['error_body'] = exc.read().decode(errors='replace')
                dest.write_text(json.dumps(record, ensure_ascii=False, indent=2))
                raise
            dest.write_text(json.dumps(record, ensure_ascii=False, indent=2))
            row = {k: record[k] for k in
                   ('arm', 'mode', 'case_id', 'role', 'seconds', 'stats')}
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    targets = [r for r in rows if r['role'].startswith('target')]
    valid = [r for r in targets if r['stats']['has_final_content']]
    unfaithful = [r for r in targets if r['stats'].get('prompt_faithful') is False]
    summary = {'arm': a.arm, 'mode': a.mode, 'sampling_profile': sampling,
               'overrides': overrides,
               'instrumented': instrument, 'seed': a.seed,
               'requests': len(targets), 'with_final_content': len(valid),
               'with_han': sum(bool(r['stats']['final_han']) for r in valid),
               'with_other_script': sum(bool(r['stats']['final_other_script']) for r in valid),
               'truncated': sum(r['stats']['finish_reason'] == 'length' for r in targets),
               'prompt_token_mismatches': len(unfaithful),
               'unicode_version': unicodedata.unidata_version, 'rows': rows}
    (a.out/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    if unfaithful:
        print(f'WARNING: {len(unfaithful)} target request(s) did not match '
              f'expected_prompt_tokens; the replayed prompt is not faithful.', flush=True)

if __name__ == '__main__':
    main()
