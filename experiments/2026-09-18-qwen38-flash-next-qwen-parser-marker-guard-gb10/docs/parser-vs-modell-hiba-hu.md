# Az „eltűnő válasz" két különböző hibája — szétválasztva

**2026-09-18 · spark-dev (GB10) · round6**

## 1. Parser-oldali hiba (a patch 12 + 13 ezt javítja)

Mérés: [`code/parser_config_probe.py`](../code/parser_config_probe.py), a **valódi `qwen3_coder`
úton szerzett** parser-configgal (nem a tesztek alapértelmezett `qwen3_config()`-jával), három
streaming-darabolással (1 / 7 / 10000 karakter). Mindhárom darabolás azonos eredményt adott.

Három állapotban mérve — a „csak patch 12" változat úgy készült, hogy a régi image
site-packages-ére futásidőben csak a `qwen-tool-preamble.patch` ment fel:

| eset | nincs patch | csak patch 12 | patch 12+13 |
|---|---|---|---|
| ` ```xml ` blokkban bemutatott hívás | fantom hívás, **40%** | fantom hívás, **40%** | nincs hívás, **100%** |
| prózában idézett `<tool_call>` | nincs hívás, **4%** | nincs hívás, **100%** | nincs hívás, **100%** |
| valódi hívás | parse-olódik | parse-olódik | parse-olódik |
| unfenced `<tool_call>` reasoningben | fantom hívás, 51% | 51% | 51% |

Az attribúció tehát saját mérés, nem átvett állítás: a **patch 12 a saját esetét javítja**, de a
kódblokkoshoz **egyáltalán nem nyúl**; a fantom hívást és a `content: null`-t a **patch 13**
szünteti meg; és egyik sem okoz regressziót a valódi híváson.

Két pontosítás a szakirodalmi leíráshoz képest:

- A patch 12 esete a régi image-en **nem** fantom hívást okozott, hanem szövegvesztést
  (84 karakterből 3 maradt). A `content: null` a patch 13 territóriuma.
- A guardok a forrásban `name == "qwen3"`-ra kötöttek. A receptünk `--tool-call-parser qwen3_coder`-t
  használ, de a lánc `Qwen3EngineToolParser` → `Qwen3ParserToolAdapter` → `Qwen3Parser`, ahol
  `CONFIG_NAME = "qwen3"` — a szonda visszaigazolta: `validate_tool_preamble=True`,
  `guard_literal_tool_markers=True`. **A javítás a mi konfigurációnkon aktív.**

## 2. Modell-oldali hiba (semmilyen parser-patch nem javítja)

Prompt: `Magyarazd el a <tool_call> literal sztringet, eszkozhivas nelkul.`, tools a kérésben.

A `/v1/chat/completions/render` → `/v1/completions` úton a tool- és reasoning-parser teljesen
ki van kapcsolva. A nyers generálás **819 karakter, 196 token, `finish_reason = stop`**.

Az utolsó hat token:

```
' `'   '<tool_call>'   '`'   ' and'   ' `'   '<|im_end|>'
```

A modell **maga adta ki az EOS-t** (`<|im_end|>`, id 248046) mondat közepén, még a `<think>`-en
belül, `</think>` és válasz nélkül. A `<tool_call>` négyszer szerepel a 819 karakteres fordulóban
(a 45., 114., 216. és 801. pozíción); a token-kiíratás szerint az utolsó **speciális tokenként**
tokenizálódott, és két tokennel utána jött az EOS.

**Következmény:** ez nem serving-, hanem modell-/sablon-szintű hiba.

- A patch 13 fence-alapú guardja elvileg sem foghatja meg: itt a modell a valódi speciális tokent
  emittálja, nem szöveget, így nincs mit „szövegként megtartani".
- Mivel a determinisztikus Top-K `.so` bitre azonos a két image-ben és a checkpoint ugyanaz,
  a nyers token-szekvencia image-független: ez a hiba a mai változás előtt és után is azonos.

## Amit ez együtt jelent

A blazux patch 12+13 valódi, mérhető javítás, és a mi pinelt konfigurációnkon aktív. De az
agentic „eltűnő válasz" incidenseink egy része **nem ez** — azt a modell EOS-viselkedése okozza.
A két okot itt sikerült először külön mérésre bontani.

Gyakorlati következmény a DocIT agentekre: a `tools` jelenléte a kérésben érdemben növeli a
kockázatot (ugyanaz a prompt `tools` nélkül 878 karakteres választ adott, `tools`-szal nullát),
és a triggert a modell saját reasoningje állítja elő, nem a felhasználói szöveg.
