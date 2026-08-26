# D3b újramérés — előre rögzített protokoll

**Rögzítve:** 2026-08-26, a futtatás ELŐTT (a dolgozat bírálati jelentésének 1. blokkoló pontja nyomán).

## Miért

Az eredeti D3b (`analyze_d.py`) a forrásnyelvi fogalom SAE-feature-készletét a hozzá rendelt
**kontrollszó** (`control.en`: *help*, *friendship*, …) angol promptjával vetette össze, nem az előre
rögzített **angol közelítőszóval** (`en_approx`: *mutual aid*, *love*, …). A dolgozat állítása
(„húz-e a fogalom a saját angol közelítőszava felé") tehát mérve nem volt. Az eredeti számítás
ezentúl „szemantikai szomszéd"-tesztként marad meg, a fordítási hipotézis tesztje az alábbi.

## Kérdés és hipotézis

Ha a modell a lefordíthatatlan fogalmat az angol közelítésen keresztül éri el, a forrásnyelvi
prompt (pl. „Mit jelent a magyar »kaláka« szó?") középső rétegbeli feature-készlete közelebb áll
a SAJÁT közelítőszó angol promptjához („What does the expression 'mutual aid' mean?"), mint MÁS
fogalmak közelítőszavainak promptjaihoz.

- **H_pivot:** a többlet (saját − mások átlaga) pozitív a fogalmak többségénél.
- **H_0:** a többlet 0 körül szór.

## Anyag

- 16 új angol prompt: `prompts_d3b.jsonl` (`build_prompts_d3b.py`). Sablon = a kontrollszó-prompt
  sablonja (`What does the word/expression '…' mean?`), a keret így bitre azonos a meglévő
  kontrollpromptokkal. A közelítőszó = az `en_approx` első, `/` előtti alternatívája, zárójel és
  belső idézőjel nélkül (a szabály a szkriptben, a 16 kész prompt a fájlban, futtatás előtt kiírva).
- Modell: `Qwen/Qwen3.5-9B-Base`, nyers folytatás, greedy, azonos kód (`run.py`, `run_sae.py`),
  külön eredmény-könyvtár (`results_d3b`). A forrásnyelvi fogalom-promptok SAE-fájljai a
  meglévő `results/sae/`-ből jönnek (azonos modell, azonos kód, batch = 1 → determinisztikus).
- Ha marad idő: ugyanez az instruct modellen chat-sablonnal (`results_d3b_instruct`), a 2. kör
  `results_instruct/sae/`-jével párban. Ez másodlagos.

## Mérés (előre rögzítve)

- **Réteg:** elsődleges a **10.** (az eredeti D3/D3b rétege, a Mérés C UNI-csúcsa 9–11);
  másodlagos a 16. (a Mérés C előre rögzített tesztrétege). Más réteget utólag nem választunk.
- **Halmaz:** a prompt tokenjeinek feature-UNIÓJA a kérdés token-tartományán (`q_tok_span`),
  ahogy a Mérés C-ben; másodlagosan a teljes prompt uniója (az eredeti D3b-vel összevethető).
- **Távolság:** Jaccard.
- **Statisztika fogalmanként:** többlet = J(forrás, saját közelítő) − átlag_{15 másik} J(forrás, másik közelítő).
- **Elsődleges próba:** exakt előjelteszt a 16 többleten (kétoldali). Másodlagos: Wilcoxon
  (scipy, `wilcoxon(..., zero_method="wilcox", alternative="two-sided")`) és a többlet átlagának
  fogalom-szintű bootstrap 95% CI-je (2000 minta, seed 0).
- **Hossz-illesztés:** a „másik" közelítők halmazát szűkítve is számoljuk azokra, amelyek
  kérdés-token-száma legfeljebb 1-gyel tér el a sajáttól; ha egy fogalomnál < 3 ilyen marad,
  a fogalom ebből a változatból kimarad (a szám a riportban).
- **Legkisebb érdekes hatás (SESOI):** +0,02 Jaccard-többlet. Indok: a Mérés C-ben az azonos
  item nyelvközi többlete a 16. rétegen a leggyengébb cellában is ennek a nagyságrendjében
  vagy fölötte volt; egy angol pivotnak ennek legalább a felét hoznia kellene.
- **Döntési szabály:** „pozitív evidencia a pivotra" = előjelteszt p < 0,05 ÉS átlagos többlet
  ≥ SESOI. „Nincs pozitív evidencia" = minden más; ez NEM a pivot hiányának bizonyítéka. Ha a
  CI teljes egészében a SESOI alatt van, azt „a mért lexikai pivot-hatás kisebb, mint +0,02"
  formában közöljük.

## Amit ez a teszt sem mér

Egy elosztott, nem lexikális angol pivotot; a közelítőszó-prompt maga is csak egy angol
megfogalmazás a sok közül. A D2 pozitív kontrolljához hasonlóan itt is jelezni kell a műszer
érzékenységét: a forrásnyelvi fogalom J-je a SAJÁT angol kérdéséhez (D3 első oszlopa) a felső
referencia.

## Kiegészítés (2026-08-26, az elsődleges eredmény MEGTEKINTÉSE UTÁN — feltáró, nem konfirmatív)

Az elsődleges elemzés pozitív többletet adott (a riportban). Ez a teszt azonban **nem különbözteti
meg** a lexikális angol pivotot (R2) a nyelvfüggetlen jelentés-közelségtől (R3): egy közös fogalmi
térben a *kaláka* akkor is közelebb áll a *mutual aid*-hez, mint a *kiss*-hez, ha angol
közvetítés nincs. A megkülönböztető kérdés: **a vonzás angol-specifikus-e?** Ehhez a közelítő
kifejezés HARMADIK nyelvű változata kell (hu-forrású fogalomnál kínai, zh-forrásúnál magyar):

- H_R2 (angol pivot): J(forrás, angol közelítő) > J(forrás, harmadik nyelvű közelítő), párosan.
- H_R3 (nyelvfüggetlen): a kettő nem különbözik.

Anyag: `prompts_d3b_x.jsonl` (`build_prompts_d3b_x.py`), 16 prompt, a kontrollszó-prompt
nyelvi sablonjával; a fordításokat a szerző adta meg a futtatás előtt (a szkriptben). Réteg és
tartomány mint fent (10 · kérdés). Próba: exakt előjelteszt a 16 páros különbségen; SESOI +0,02.
⚠️ Ismert torzítás: a kínai kérdés kevesebb tokenből áll, az unió kisebb, a Jaccard ettől is
mozoghat; ezért a különbséget a harmadik nyelvű KONTROLLSZÓ-prompt (meglévő `-ctrl` zh/hu)
ugyanilyen párosával is összevetjük (különbség-a-különbségben).
