"""01-es kör — az általános eszközkatalógus és a MASSIVE-leképezés (01-runbook 3.5).

Olyan eszközök, amelyeket sok rendszer használ (időjárás, e-mail, keresés, naptár, …). Mindegyikhez név,
magyar és angol leírás, JSON-paraméterséma (angol `description` + magyar `leiras`) és a közeli párok a nehéz
zavaráshoz. A MASSIVE 60 intentje egy-egy eszközre vagy `X`-re képeződik; ahol a közeli pár a MASSIVE-mondatokon
is helyes lehet, a leképezés `felulvizsgal` jelzést kap, és az F1 LLM-átnézése dönt (a 00 F1F tanulsága).

  python3 kor01/eszkozok/katalogus_epit.py   → kor01/katalogus/{eszkozok.json, massive_lekepezes.json}
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def P(name, typ, req, en, hu, enum=None):
    d = {"name": name, "type": typ, "required": req, "description": en, "leiras": hu}
    if enum:
        d["enum"] = enum
    return d


def T(name, domain, hu, en, params, massive=(), kozeli=(), felulvizsgal=()):
    return {"name": name, "domain": domain, "leiras": hu, "description": en, "params": params,
            "massive": list(massive), "kozeli": list(kozeli), "felulvizsgal": list(felulvizsgal)}


LOC = P("location", "string", True, "City or place name.", "Település vagy hely neve.")
DATE = P("date", "string", False, "Date in YYYY-MM-DD; default today.", "Dátum ÉÉÉÉ-HH-NN formában; alapból ma.")

TOOLS = [
    # --- időjárás ---
    T("get_weather", "időjárás", "Aktuális időjárás vagy előrejelzés egy helyre és napra: hőmérséklet, csapadék, szél.",
      "Current weather or forecast for a place and day: temperature, precipitation, wind.", [LOC, DATE],
      massive=["weather_query"], kozeli=["get_air_quality"]),
    T("get_air_quality", "időjárás", "Levegőminőség-index és pollenterhelés egy helyen.",
      "Air quality index and pollen levels at a place.", [LOC], kozeli=["get_weather"]),
    # --- e-mail és névjegyek ---
    T("send_email", "e-mail", "Új e-mail küldése egy vagy több címzettnek, tárggyal és szöveggel.",
      "Send a new email to one or more recipients with a subject and body.",
      [P("to", "array", True, "Recipient addresses or contact names.", "Címzettek címe vagy névjegyneve."),
       P("subject", "string", False, "Subject line.", "Tárgy."),
       P("body", "string", True, "Message body.", "Az üzenet szövege.")],
      massive=["email_sendemail"], kozeli=["reply_email", "send_sms"], felulvizsgal=["reply_email"]),
    T("reply_email", "e-mail", "Válasz egy meglévő e-mailre az eredeti szálban.",
      "Reply to an existing email in its original thread.",
      [P("message_id", "string", True, "Id of the email being answered.", "A megválaszolt e-mail azonosítója."),
       P("body", "string", True, "Reply text.", "A válasz szövege."),
       P("reply_all", "boolean", False, "Reply to all recipients.", "Válasz mindenkinek.")],
      kozeli=["send_email"]),
    T("search_email", "e-mail", "E-mailek keresése vagy listázása feladó, tárgy, dátum vagy olvasatlanság szerint.",
      "Search or list emails by sender, subject, date or unread status.",
      [P("query", "string", False, "Free-text search.", "Szabad szöveges keresés."),
       P("sender", "string", False, "Sender name or address.", "Feladó neve vagy címe."),
       P("unread_only", "boolean", False, "Only unread messages.", "Csak az olvasatlanok.")],
      massive=["email_query"], kozeli=["search_documents"]),
    T("add_contact", "e-mail", "Új névjegy felvétele névvel, e-mail-címmel, telefonszámmal.",
      "Add a new contact with name, email address and phone number.",
      [P("name", "string", True, "Contact name.", "Név."), P("email", "string", False, "Email address.", "E-mail-cím."),
       P("phone", "string", False, "Phone number.", "Telefonszám.")],
      massive=["email_addcontact"], kozeli=["get_contact"]),
    T("get_contact", "e-mail", "Egy névjegy adatainak lekérdezése: e-mail, telefon, cím, születésnap.",
      "Look up a contact's details: email, phone, address, birthday.",
      [P("name", "string", True, "Contact name.", "Név."),
       P("field", "string", False, "Requested field.", "A kért adat.", ["email", "phone", "address", "birthday"])],
      massive=["email_querycontact"], kozeli=["add_contact"]),
    T("send_sms", "üzenet", "SMS vagy azonnali üzenet küldése telefonszámra vagy névjegynek.",
      "Send a text message to a phone number or contact.",
      [P("to", "string", True, "Phone number or contact name.", "Telefonszám vagy névjegy."),
       P("text", "string", True, "Message text.", "Az üzenet szövege.")], kozeli=["send_email"]),
    # --- naptár és időpontok ---
    T("create_event", "naptár", "Új esemény felvétele a naptárba időponttal, hellyel, résztvevőkkel.",
      "Create a calendar event with time, place and attendees.",
      [P("title", "string", True, "Event title.", "Az esemény címe."),
       P("start", "string", True, "Start, ISO 8601.", "Kezdés, ISO 8601."),
       P("end", "string", False, "End, ISO 8601.", "Vége, ISO 8601."),
       P("attendees", "array", False, "Attendee names or emails.", "Résztvevők.")],
      massive=["calendar_set"], kozeli=["book_appointment", "set_reminder", "list_events"],
      felulvizsgal=["set_reminder"]),
    T("list_events", "naptár", "A naptár eseményeinek lekérdezése egy időszakra vagy kulcsszóra.",
      "List calendar events for a period or keyword.",
      [P("date_from", "string", False, "Start date.", "Kezdő dátum."), P("date_to", "string", False, "End date.", "Záró dátum."),
       P("query", "string", False, "Keyword.", "Kulcsszó.")],
      massive=["calendar_query"], kozeli=["create_event", "get_holidays"]),
    T("delete_event", "naptár", "Egy naptáresemény törlése vagy lemondása.", "Delete or cancel a calendar event.",
      [P("query", "string", True, "Which event (title, date).", "Melyik esemény (cím, dátum)."), DATE],
      massive=["calendar_remove"], kozeli=["create_event"]),
    T("book_appointment", "naptár", "Időpontfoglalás külső szolgáltatónál: orvos, fodrász, autószerviz, ügyfélszolgálat.",
      "Book an appointment with an external provider: doctor, hairdresser, car service.",
      [P("provider", "string", True, "Provider name or type.", "Szolgáltató neve vagy típusa."),
       P("datetime", "string", True, "Requested time, ISO 8601.", "Kért időpont, ISO 8601.")],
      kozeli=["create_event", "book_restaurant"]),
    T("get_holidays", "naptár", "Ünnepnapok, munkaszüneti és áthelyezett munkanapok egy országban és évben.",
      "Public holidays and moved working days for a country and year.",
      [P("country", "string", False, "Country code; default HU.", "Országkód; alapból HU."),
       P("year", "integer", False, "Year.", "Év.")], kozeli=["list_events", "get_current_time"]),
    # --- ébresztő, időzítő, emlékeztető ---
    T("set_alarm", "ébresztő", "Ébresztő beállítása egy adott időpontra, opcionálisan ismétléssel.",
      "Set an alarm for a clock time, optionally repeating.",
      [P("time", "string", True, "Clock time HH:MM.", "Időpont ÓÓ:PP."), DATE,
       P("repeat", "string", False, "Repeat rule.", "Ismétlés.", ["none", "daily", "weekdays", "weekly"])],
      massive=["alarm_set"], kozeli=["set_timer", "set_reminder"], felulvizsgal=["set_timer"]),
    T("list_alarms", "ébresztő", "A beállított ébresztők listázása.", "List the alarms that are set.", [],
      massive=["alarm_query"], kozeli=["set_alarm"]),
    T("delete_alarm", "ébresztő", "Egy vagy minden ébresztő törlése.", "Delete one or all alarms.",
      [P("time", "string", False, "Which alarm; empty = all.", "Melyik ébresztő; üres = mind.")],
      massive=["alarm_remove"], kozeli=["list_alarms"]),
    T("set_timer", "ébresztő", "Visszaszámláló időzítő indítása adott időtartamra.", "Start a countdown timer for a duration.",
      [P("minutes", "number", True, "Duration in minutes.", "Időtartam percben.")], kozeli=["set_alarm"]),
    T("set_reminder", "ébresztő", "Emlékeztető egy teendőről egy adott időpontban.", "Remind about a to-do at a given time.",
      [P("text", "string", True, "What to remind about.", "Miről emlékeztessen."),
       P("time", "string", True, "When, ISO 8601.", "Mikor, ISO 8601.")], kozeli=["set_alarm", "create_task"]),
    # --- listák és feladatok ---
    T("add_to_list", "listák", "Tétel hozzáadása egy listához (pl. bevásárlólista); új lista létrehozása is.",
      "Add items to a list (e.g. shopping list); creates the list if needed.",
      [P("list_name", "string", True, "List name.", "A lista neve."), P("items", "array", True, "Items to add.", "A tételek.")],
      massive=["lists_createoradd"], kozeli=["create_task", "remove_from_list"]),
    T("get_list", "listák", "Egy lista tartalmának lekérdezése.", "Show the contents of a list.",
      [P("list_name", "string", True, "List name.", "A lista neve.")], massive=["lists_query"], kozeli=["add_to_list"]),
    T("remove_from_list", "listák", "Tétel törlése egy listáról, vagy a lista törlése.", "Remove items from a list or delete the list.",
      [P("list_name", "string", True, "List name.", "A lista neve."), P("items", "array", False, "Items; empty = whole list.", "Tételek; üres = az egész lista.")],
      massive=["lists_remove"], kozeli=["add_to_list"]),
    T("create_task", "listák", "Feladat létrehozása a feladatkezelőben határidővel és felelőssel.",
      "Create a task in the task manager with a due date and assignee.",
      [P("title", "string", True, "Task title.", "A feladat címe."), P("due", "string", False, "Due date.", "Határidő."),
       P("assignee", "string", False, "Assignee.", "Felelős.")], kozeli=["add_to_list", "set_reminder"]),
    # --- keresés és tudás ---
    T("web_search", "keresés", "Általános webes keresés tényekre, személyekre, eseményekre.",
      "General web search for facts, people and events.",
      [P("query", "string", True, "Search query.", "Keresőkifejezés.")], massive=["qa_factoid"],
      kozeli=["get_news", "define_word", "search_documents"], felulvizsgal=["get_news"]),
    T("define_word", "keresés", "Szó vagy kifejezés jelentése szótárból.", "Dictionary definition of a word or phrase.",
      [P("term", "string", True, "Word or phrase.", "Szó vagy kifejezés.")], massive=["qa_definition"],
      kozeli=["web_search", "translate_text"]),
    T("calculate", "keresés", "Matematikai kifejezés kiszámítása.", "Evaluate a mathematical expression.",
      [P("expression", "string", True, "Expression.", "Kifejezés.")], massive=["qa_maths"], kozeli=["convert_currency"]),
    T("convert_currency", "pénzügy", "Összeg átváltása devizák között az aktuális árfolyamon.",
      "Convert an amount between currencies at the current rate.",
      [P("amount", "number", False, "Amount; default 1.", "Összeg; alapból 1."), P("from_currency", "string", True, "Source currency.", "Forrásdeviza."),
       P("to_currency", "string", True, "Target currency.", "Céldeviza.")], massive=["qa_currency"], kozeli=["get_stock_quote", "calculate"]),
    T("get_stock_quote", "pénzügy", "Részvény vagy index aktuális árfolyama.", "Current price of a stock or index.",
      [P("symbol", "string", True, "Ticker or company name.", "Ticker vagy cégnév.")], massive=["qa_stock"], kozeli=["convert_currency"]),
    T("translate_text", "keresés", "Szöveg fordítása másik nyelvre.", "Translate text into another language.",
      [P("text", "string", True, "Text.", "Szöveg."), P("target_language", "string", True, "Target language.", "Célnyelv.")],
      kozeli=["define_word"]),
    T("search_documents", "keresés", "Keresés a saját dokumentumok és fájlok között.", "Search the user's own documents and files.",
      [P("query", "string", True, "Search query.", "Keresőkifejezés.")], kozeli=["web_search", "search_email"]),
    T("get_news", "hírek", "Friss hírek témára, forrásra vagy országra.", "Latest news by topic, source or country.",
      [P("topic", "string", False, "Topic.", "Téma."), P("source", "string", False, "News source.", "Hírforrás.")],
      massive=["news_query"], kozeli=["web_search"]),
    # --- idő ---
    T("get_current_time", "idő", "Pontos idő, dátum vagy a hét napja, opcionálisan más időzónában.",
      "Current time, date or weekday, optionally in another time zone.",
      [P("location", "string", False, "Place or time zone.", "Hely vagy időzóna.")], massive=["datetime_query"],
      kozeli=["convert_timezone", "get_holidays"]),
    T("convert_timezone", "idő", "Időpont átszámítása időzónák között.", "Convert a time between time zones.",
      [P("time", "string", True, "Time.", "Időpont."), P("from_zone", "string", True, "Source zone.", "Forrászóna."),
       P("to_zone", "string", True, "Target zone.", "Célzóna.")], massive=["datetime_convert"], kozeli=["get_current_time"]),
    # --- média ---
    T("play_music", "média", "Zene lejátszása előadó, dal, album, műfaj vagy lejátszási lista szerint.",
      "Play music by artist, song, album, genre or playlist.",
      [P("query", "string", True, "What to play.", "Mit játsszon.")], massive=["play_music"], kozeli=["play_radio", "play_podcast"]),
    T("play_radio", "média", "Rádióállomás lejátszása.", "Play a radio station.",
      [P("station", "string", True, "Station name or frequency.", "Állomás neve vagy frekvenciája.")], massive=["play_radio"], kozeli=["play_music"]),
    T("play_podcast", "média", "Podcast vagy podcastepizód lejátszása.", "Play a podcast or episode.",
      [P("show", "string", True, "Show or episode.", "Műsor vagy epizód.")], massive=["play_podcasts"], kozeli=["play_audiobook"]),
    T("play_audiobook", "média", "Hangoskönyv lejátszása vagy folytatása.", "Play or resume an audiobook.",
      [P("title", "string", True, "Book title.", "A könyv címe.")], massive=["play_audiobook"], kozeli=["play_podcast"]),
    T("rate_song", "média", "Az éppen szóló dal kedvelése vagy nemtetszés jelölése.", "Like or dislike the current song.",
      [P("rating", "string", True, "Rating.", "Értékelés.", ["like", "dislike"])],
      massive=["music_likeness", "music_dislikeness"], kozeli=["get_now_playing"]),
    T("get_now_playing", "média", "Információ az éppen szóló dalról: cím, előadó, album.", "Info about the song now playing.",
      [], massive=["music_query"], kozeli=["rate_song"]),
    T("set_player_mode", "média", "Lejátszó módja: keverés, ismétlés, ugrás.", "Player mode: shuffle, repeat, skip.",
      [P("mode", "string", True, "Mode.", "Mód.", ["shuffle", "repeat", "skip", "previous"])], massive=["music_settings"],
      kozeli=["set_volume"]),
    T("set_volume", "média", "Hangerő növelése, csökkentése vagy beállítása.", "Increase, decrease or set the volume.",
      [P("level", "integer", False, "Absolute level 0–100.", "Abszolút szint 0–100."),
       P("direction", "string", False, "Relative change.", "Relatív változás.", ["up", "down"])],
      massive=["audio_volume_up", "audio_volume_down", "audio_volume_other"], kozeli=["mute_audio"]),
    T("mute_audio", "média", "Hang némítása vagy visszakapcsolása.", "Mute or unmute audio.",
      [P("mute", "boolean", True, "True = mute.", "Igaz = némítás.")], massive=["audio_volume_mute"], kozeli=["set_volume"]),
    T("start_game", "média", "Egyszerű szöveges vagy kvízjáték indítása.", "Start a simple text or quiz game.",
      [P("game", "string", False, "Game name.", "A játék neve.")], massive=["play_game"]),
    # --- okosotthon ---
    T("set_lights", "okosotthon", "Világítás ki- és bekapcsolása, fényerő és szín állítása helyiségenként.",
      "Turn lights on or off, set brightness and colour per room.",
      [P("room", "string", False, "Room.", "Helyiség."), P("power", "string", False, "On or off.", "Be vagy ki.", ["on", "off"]),
       P("brightness", "integer", False, "Brightness 0–100.", "Fényerő 0–100."), P("color", "string", False, "Colour.", "Szín.")],
      massive=["iot_hue_lightchange", "iot_hue_lightdim", "iot_hue_lightup", "iot_hue_lightoff", "iot_hue_lighton"],
      kozeli=["smart_plug"]),
    T("smart_plug", "okosotthon", "Okos konnektorra kötött eszköz be- vagy kikapcsolása.", "Switch a device on a smart plug on or off.",
      [P("device", "string", True, "Device.", "Eszköz."), P("state", "string", True, "State.", "Állapot.", ["on", "off"])],
      massive=["iot_wemo_on", "iot_wemo_off"], kozeli=["set_lights"]),
    T("start_vacuum", "okosotthon", "Robotporszívó indítása vagy leállítása.", "Start or stop the robot vacuum.",
      [P("action", "string", True, "Action.", "Művelet.", ["start", "stop", "dock"])], massive=["iot_cleaning"]),
    T("make_coffee", "okosotthon", "Kávéfőzés indítása az okos kávéfőzőn.", "Start brewing on the smart coffee maker.",
      [P("type", "string", False, "Drink type.", "Ital típusa.")], massive=["iot_coffee"]),
    T("set_thermostat", "okosotthon", "A fűtés vagy hűtés célhőmérsékletének beállítása.", "Set the heating or cooling target temperature.",
      [P("temperature", "number", True, "Target °C.", "Cél °C."), P("room", "string", False, "Room.", "Helyiség.")],
      kozeli=["get_weather"]),
    # --- közlekedés ---
    T("plan_trip", "közlekedés", "Útvonal- és menetrend-tervezés A-ból B-be: indulások, átszállások, menetidő.",
      "Plan a route and timetable from A to B: departures, transfers, travel time.",
      [P("origin", "string", False, "From; default current location.", "Honnan; alapból a jelenlegi hely."),
       P("destination", "string", True, "To.", "Hová."), P("mode", "string", False, "Mode.", "Mód.", ["car", "transit", "walk", "bike"])],
      massive=["transport_query"], kozeli=["get_traffic", "buy_ticket"]),
    T("get_traffic", "közlekedés", "Forgalmi helyzet, dugók, útlezárások egy útvonalon vagy területen.",
      "Traffic conditions, jams and closures on a route or area.",
      [P("area", "string", True, "Road or area.", "Út vagy terület.")], massive=["transport_traffic"], kozeli=["plan_trip"]),
    T("book_taxi", "közlekedés", "Taxi rendelése egy címre.", "Order a taxi to an address.",
      [P("pickup", "string", True, "Pickup address.", "Felvételi cím."), P("destination", "string", False, "Destination.", "Cél.")],
      massive=["transport_taxi"], kozeli=["buy_ticket"]),
    T("buy_ticket", "közlekedés", "Vonat-, busz- vagy repülőjegy vásárlása.", "Buy a train, bus or plane ticket.",
      [P("origin", "string", True, "From.", "Honnan."), P("destination", "string", True, "To.", "Hová."), DATE],
      massive=["transport_ticket"], kozeli=["plan_trip", "book_taxi"]),
    # --- étel, vásárlás ---
    T("order_food", "étel", "Étel rendelése kiszállítással vagy elvitelre.", "Order food for delivery or takeaway.",
      [P("restaurant", "string", False, "Restaurant.", "Étterem."), P("items", "array", True, "Dishes.", "Ételek.")],
      massive=["takeaway_order"], kozeli=["book_restaurant", "get_restaurant_info"]),
    T("get_restaurant_info", "étel", "Étterem adatai: nyitvatartás, kiszállítás, menü, értékelés.",
      "Restaurant details: opening hours, delivery, menu, rating.",
      [P("restaurant", "string", True, "Restaurant.", "Étterem.")], massive=["takeaway_query"],
      kozeli=["order_food", "find_places", "track_package"], felulvizsgal=["track_package"]),
    T("book_restaurant", "étel", "Asztalfoglalás étterembe.", "Book a table at a restaurant.",
      [P("restaurant", "string", True, "Restaurant.", "Étterem."), P("datetime", "string", True, "Time.", "Időpont."),
       P("people", "integer", False, "Party size.", "Létszám.")], kozeli=["order_food", "book_appointment"]),
    T("find_recipe", "étel", "Recept keresése étel vagy hozzávaló szerint, főzési útmutatóval.",
      "Find a recipe by dish or ingredient, with cooking instructions.",
      [P("query", "string", True, "Dish or ingredient.", "Étel vagy hozzávaló.")], massive=["cooking_recipe", "cooking_query"]),
    T("track_package", "vásárlás", "Csomag vagy rendelés nyomon követése azonosító alapján.", "Track a parcel or order by its id.",
      [P("tracking_id", "string", True, "Tracking or order id.", "Követési vagy rendelésszám.")], kozeli=["get_restaurant_info"]),
    # --- ajánlás ---
    T("find_events", "ajánlás", "Programok, koncertek, kiállítások keresése helyre és időre.", "Find events, concerts and exhibitions by place and time.",
      [LOC, DATE], massive=["recommendation_events"], kozeli=["find_places", "list_events"]),
    T("find_places", "ajánlás", "Helyek ajánlása: étterem, kávézó, bolt, látnivaló a közelben.", "Recommend places nearby: restaurant, café, shop, sight.",
      [P("category", "string", True, "Kind of place.", "A hely típusa."), LOC], massive=["recommendation_locations"],
      kozeli=["find_events", "get_restaurant_info"]),
    T("recommend_movies", "ajánlás", "Film- vagy sorozatajánlás műfaj, szereplő vagy hangulat szerint.", "Recommend films or series by genre, actor or mood.",
      [P("query", "string", False, "Preferences.", "Preferenciák.")], massive=["recommendation_movies"]),
    # --- közösségi és ügyfélszolgálat ---
    T("post_social", "közösségi", "Bejegyzés vagy panasz közzététele közösségi oldalon.", "Post an update or complaint on social media.",
      [P("platform", "string", False, "Platform.", "Platform."), P("text", "string", True, "Post text.", "A bejegyzés szövege.")],
      massive=["social_post"], kozeli=["get_social_feed", "create_support_ticket"], felulvizsgal=["create_support_ticket"]),
    T("get_social_feed", "közösségi", "Közösségi hírfolyam vagy egy ismerős friss bejegyzései.", "Social feed or a friend's latest posts.",
      [P("person", "string", False, "Whose posts.", "Kinek a bejegyzései.")], massive=["social_query"], kozeli=["post_social"]),
    T("create_support_ticket", "ügyfélszolgálat", "Hibajegy vagy panasz nyitása egy cég ügyfélszolgálatánál.", "Open a support ticket or complaint with a company.",
      [P("company", "string", True, "Company.", "Cég."), P("issue", "string", True, "Problem description.", "A probléma leírása.")],
      kozeli=["post_social", "send_email"]),
]

X_INTENTS = {"general_greet": "köszönés, nincs eszköz", "general_joke": "vicc kérése, eszköz nélkül válaszolható",
             "general_quirky": "csevegés, eszköz nélkül"}


def main() -> None:
    names = [t["name"] for t in TOOLS]
    dup = [n for n, c in Counter(names).items() if c > 1]
    assert not dup, f"ismétlődő eszköznév: {dup}"
    for t in TOOLS:
        for k in t["kozeli"] + t["felulvizsgal"]:
            assert k in names, f"{t['name']}: ismeretlen közeli pár: {k}"
    mapping = {}
    for t in TOOLS:
        for i in t["massive"]:
            assert i not in mapping, f"{i} kétszer leképezve"
            mapping[i] = {"eszkoz": t["name"], "felulvizsgal": t["felulvizsgal"]}
    for i, why in X_INTENTS.items():
        mapping[i] = {"eszkoz": None, "ok": why, "felulvizsgal": []}
    hu = [json.loads(line) for line in open(ROOT / "forras/massive/1.1/data/hu-HU.jsonl")]
    intents = {r["intent"] for r in hu}
    missing = sorted(intents - set(mapping))
    assert not missing, f"leképezetlen MASSIVE-intentek: {missing}"
    out = ROOT / "katalogus"
    out.mkdir(exist_ok=True)
    (out / "eszkozok.json").write_text(json.dumps(TOOLS, ensure_ascii=False, indent=1))
    (out / "massive_lekepezes.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=1, sort_keys=True))
    per_tool = Counter(m["eszkoz"] for i, m in mapping.items() for r in hu if r["intent"] == i and r["partition"] == "test")
    print(f"eszközök: {len(TOOLS)} · domének: {len({t['domain'] for t in TOOLS})} · MASSIVE-intentek: {len(intents)} "
          f"(ebből X: {len(X_INTENTS)}) · MASSIVE nélküli eszközök: {sum(not t['massive'] for t in TOOLS)}")
    print(f"felülvizsgálandó intentek: {sorted(i for i, m in mapping.items() if m['felulvizsgal'])}")
    print(f"hu test mondatok eszközönként (top 8): {per_tool.most_common(8)}")


if __name__ == "__main__":
    main()
