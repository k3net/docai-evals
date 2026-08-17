# DocAI Evals — magyar összefoglaló

**Reprodukálható mérések magyar dokumentum-AI-hoz:** kinyerési pontosság, üzletileg kritikus
hibakapuk, modell-összehasonlítások és DGX Spark (GB10) inferencia-teljesítmény.

Ez a repository a **[docai.hu/blog](https://docai.hu/blog)** mérnöki cikkeinek *bizonyítéktára*.
A cikkben a történet és a tanulság van; itt a módszertan, a konfiguráció, a nyers számok — és
szándékosan a negatív eredmények is.

> A DocAI magyar dokumentumfeldolgozó és dokumentum-AI platform: OCR → irattípus-osztályozás →
> kulcsinformáció-kinyerés (KIE) → üzleti validálás → chat a saját dokumentumaid felett.
> Termékoldal: **[docai.hu](https://docai.hu)**

---

## Miért van ez a repository?

A publikált LLM-benchmarkok többsége angol nyelvű, generikus feladatot mér, adatközponti GPU-n.
Mi egy éles rendszert üzemeltetünk, ami szűkebb és nehezebb terep:

- **magyar üzleti dokumentumok** — számla, bérjegyzék, szerződés, bankszámlakivonat;
- **szigorú JSON kulcsinformáció-kinyerés**, ahol egy elrontott adószám nem elvesztett
  benchmark-pont, hanem valódi könyvelési hiba;
- **egyetlen 128 GB-os DGX Sparkon (GB10, `sm_121a`)**, nem H100/B200 flottán.

Minden publikált következtetésünknek ezt a környezetet kell kibírnia. Az itt közölt eredmények
közül több **negatív**: egy kvantálási formátum, amire nem váltottunk; egy gyártó által ajánlott
kernel-backend, ami a mi vasunkon 3×-osan lassabbnak bizonyult; egy nagyobb modell, ami veszített
a kisebbel szemben azon a feladaton, ami számít. Ezek a leghasznosabbak.

Egy mérés szándékosan kilép az üzleti dokumentumok köréből: a
[lora-vs-reranker-hu-verse](experiments/2026-08-14-lora-vs-reranker-hu-verse/) a finomhangolást
méri egy tanulás nélküli baseline ellen, magyar közkincs verseken. A kérdés — megéri-e egy LoRA,
vagy egy determinisztikus pontozó ugyanazt hozná — pontosan az, amivel éles, nem publikálható
szövegeken is szembesülünk. A közkincs korpusszal **R1** szinten megválaszolható: végig
reprodukálható, pontos számokkal, visszatartás nélkül.

## Mi kerül ki és mi nem?

| Publikált | Nem publikált |
|---|---|
| Mérési módszertan és pontozó kód | Valódi ügyféldokumentum |
| Futtatási konfiguráció, indítási flagek, motorverziók | Személyes vagy céges bizalmas adat |
| Szintetikus mintadokumentumok és ground truth | Belső API-k, infrastruktúra, éles titkok |
| Aggregált eredmények, ábrák, negatív leletek | Nem dokumentált vagy nem összevethető szám |
| A mérésből született termékdöntés | A DocAI alkalmazás forráskódja |

A teljes szabályrendszer: **[docs/data-policy.md](docs/data-policy.md)**.

## A mérések

| Mérés | A kérdés | Az eredmény |
|---|---|---|
| [moe-kernel-tuning-gb10](experiments/2026-04-14-moe-kernel-tuning-gb10/) | Segít-e a kitunolt MoE kernel a valódi kiszolgálásban? | Nem — viszont kiderült, hogy egy rutin motorfrissítés 5 %-os visszaesés volt |
| [qwen36-mtp-ab-gb10](experiments/2026-04-18-qwen36-mtp-ab-gb10/) | Megéri-e bekapcsolni a spekulatív dekódolást élesben? | Igen — és ott segít a legtöbbet, ahol az elmélet szerint a legkevesebbet kéne |
| [gemma4-vs-qwen36-json-kie](experiments/2026-04-30-gemma4-vs-qwen36-json-kie/) | Leváltható-e a KIE-modell egy alternatív nyílt modellel magyar számlákon? | Nem — a tételsor-kinyerés összeomlik, miközben a fejlécmezők hihetőnek látszanak |
| [qwen35-122b-nvfp4-bringup-gb10](experiments/2026-05-22-qwen35-122b-nvfp4-bringup-gb10/) | Mibe kerül egy 122B MoE kiszolgálása egyetlen 128 GB-os gépen? | Elfér, és a spekulatív dekódolás teszi használhatóvá |
| [35b-vs-122b-business-tasks](experiments/2026-05-22-35b-vs-122b-business-tasks/) | Mikor éri meg a négyszer nagyobb modell? | Kinyerésre nem — abban rosszabb. Több lépéses elemzésre igen: 5× kevesebb tool-hívás |
| [qwen36-fp8-vllm-flag-sweep](experiments/2026-07-01-qwen36-fp8-vllm-flag-sweep/) | Segítenek-e a gyártói „agent-ready" recept flagjei FP8 MoE-n GB10-en? | Nem — minden flag semleges vagy negatív a mi terhelésünkön |
| [qwen36-fp8-vs-nvfp4-quality](experiments/2026-07-16-qwen36-fp8-vs-nvfp4-quality/) | Megtartja-e a 4 bites NVFP4 a kinyerési minőséget? | A mezőkiemelés túléli, a több entitást összevető reasoning nem |
| [invoice-counterparty-role](experiments/2026-07-16-invoice-counterparty-role/) | Ki a partner a számlán — mi vagy ők? | Az üzletileg kritikus kapu: az NVFP4 nagyjából megduplázza a hibaarányt |
| [moe-backend-selection-gb10](experiments/2026-07-23-moe-backend-selection-gb10/) | Melyik vLLM MoE kernel-backend nyer GB10-en? | A marlin, akár 3,3×-osan — a modell kiadójának saját ajánlása ellenében |
| [mtp-speculative-decoding-gb10](experiments/2026-07-23-mtp-speculative-decoding-gb10/) | Megéri-e a multi-token prediction GB10-en? | Igen, minden mért konfiguráción — és 4 biten még inkább |
| [vllm-prod-config-tuning-gb10](experiments/2026-08-04-vllm-prod-config-tuning-gb10/) | Melyik serving-flag számít valójában élesben? | A hat javasolt mérésből kettőt volt érdemes lefuttatni; az async scheduling kikapcsolva marad |
| [lora-vs-reranker-hu-verse](experiments/2026-08-14-lora-vs-reranker-hu-verse/) | Ver-e a finomhangolás egy determinisztikus best-of-8 válogatót? | Formában nem — a tanulás nélküli válogató minden metrikán nyer. A hangon viszont csak a tanulás segít: +36 pont |

## Mérési szettek

| Szett | Mit mér |
|---|---|
| [hu-invoice-kie](evals/hu-invoice-kie/) | Mezőszintű precision / recall / F1 szigorú JSON-kinyerésre, magyar számlákon |
| [counterparty-role](evals/counterparty-role/) | A modell a *másik* céget teszi-e a partner-mezőbe — determinisztikus, üzletileg kritikus kapu |
| [chat-business-scenarios](evals/chat-business-scenarios/) | Tool-választás és több lépéses pénzügyi reasoning dokumentumkorpusz felett |
| [hu-verse-prosody](evals/hu-verse-prosody/) | Determinisztikus vonalzó a magyar versformához — szótagszám, rím, rímséma —, külső igazsághoz és kontrollcsoporthoz validálva |
| [performance](performance/) | Decode throughput, TTFT, aggregált throughput párhuzamosság alatt, spekulatív dekódolás acceptance |

## Kapcsolódó cikkek a docai.hu-n

- [Negyven százalékkal gyorsabb, és mégsem váltunk](https://docai.hu/blog/nvfp4-kvantalas-miert-nem-valtottunk) — a kvantálási döntés és a kapu, ami megfordította
- [Kövesd a gyártói doksit, és háromszor lassabb leszel](https://docai.hu/blog/backend-valasztas-gb10) — két gyártó, egy gép, ellentétes ajánlás
- [Gemma4-et néztem, MTP-t találtam](https://docai.hu/blog/gemma4-vs-qwen36) — modell-összevetés, amiből spekulatív dekódolási felismerés lett
- [122B-os modell egy DGX Sparkon: élesben mérve](https://docai.hu/blog/qwen35-122b-spark) — meddig jut egy 122B MoE 128 GB-on
- [Mikor érdemes nagyobb AI-modellt használni — és mikor nem?](https://docai.hu/blog/122b-vs-35b-mikor-jobb-a-nagyobb-modell) — 35B vs 122B valós üzleti feladatokon
- [A Qwen3.6 ott hozott, ahol nem kellett volna](https://docai.hu/blog/qwen36-mtp-gb10) — multi-token prediction négyféle terhelésen
- [Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning) — miért nem serving-nyereség a kernel-benchmark
- [Versel nekünk az AI — de tud-e Arany Jánosul?](https://docai.hu/blog/versel-nekunk-az-ai) — egy finomhangolás, ami veszített néhány tucat sor pontozókóddal szemben, és nyert azon az egy tengelyen, amit a pontozó nem lát
- Minden cikk: **[docai.hu/blog](https://docai.hu/blog)**

## Hogyan olvasd az eredményeket?

Minden mérés README-je ugyanarra a nyolc kérdésre válaszol, és az utolsó mindig az, hogy *mik a
mérés korlátai*. A visszatérő gyengeségek:

- **Kis korpuszok.** Az ember által validált magyar ground truth drága; több mérés 25–100
  dokumentumon fut. Ahol a minta nem bír el egy állítást, ott kimondjuk, és pont-becslések
  helyett McNemar-féle egzakt tesztet futtatunk.
- **Egyszeri perf-futások.** Ha nincs feltüntetve ismétlésszám, akkor variánsonként `n=1`. Az
  egyik saját workloadunkról kiderült, hogy futásról futásra **8,1 % a szórása** — ezt ott
  jelöljük, ahol felhasználjuk.
- **A mi vasunk, a mi terhelésünk.** A GB10 273 GB/s unified memóriasávszélt ad, az éles
  párhuzamosság 1–3 kérés. A kernelekre és batch-méretekre vonatkozó következtetések **nem**
  vihetők át B200-osztályú hardverre — és megjelöljük, hol bukott meg egy gyártói ajánlás pont
  emiatt.

## Ki csinálja

A **DocAI**-t a **[K3Net Kft.](https://k3.hu)** fejleszti és üzemelteti. Az itteni mérések abból az
éles rendszerből származnak, amit az ügyfeleinknek üzemeltetünk — a saját vasunkon, a valódi
dokumentumaikon, aggregált formában publikálva.

## Licenc

- A `scripts/` kód — [MIT](LICENSE)
- A dokumentáció, mérési definíciók és eredmények — [CC BY 4.0](LICENSE-DATA.md)

Forrásmegjelölés: *DocAI by K3Net Kft. — [docai.hu](https://docai.hu)*.

## Kapcsolat

**[docai.hu](https://docai.hu)** — a termék · [Blog](https://docai.hu/blog) — a cikkek ·
**[k3.hu](https://k3.hu)** — a cég
