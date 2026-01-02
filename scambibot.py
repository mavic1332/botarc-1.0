import sqlite3
import re
import requests
import time
from threading import Thread

TOKEN = ""
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
DB_FILE = "scambi.db"

# 👑 ADMIN di base (es. owner)
ADMINS = {485678878}  # puoi aggiungere altri ID se vuoi

# Modalità manutenzione
MAINTENANCE = False

# Primo
_JOLLY_A = "ArC"


# ==================== DB INIT ====================

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scambi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            initiator_id INTEGER,
            initiator_username TEXT,
            target_id INTEGER,
            target_username TEXT,
            status TEXT DEFAULT 'in_attesa',   -- in_attesa / attivo / concluso
            outcome TEXT,                     -- positivo / negativo / neutro
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS voti (
            scambio_id INTEGER,
            user_id INTEGER,
            voto INTEGER,                     -- 1 positivo, 0 negativo
            PRIMARY KEY (scambio_id, user_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS profili (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            positivi INTEGER DEFAULT 0,
            negativi INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ban (
            user_id INTEGER PRIMARY KEY,
            motivo TEXT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS moderatori (
            user_id INTEGER PRIMARY KEY,
            username TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("✅ DB pronto")


# ==================== TELEGRAM UTILS ====================

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    try:
        requests.post(f"{BASE_URL}/sendMessage", json=data)
    except Exception as e:
        print("send_message error:", e)


def edit_message_reply_markup(chat_id, message_id, reply_markup):
    data = {"chat_id": chat_id, "message_id": message_id, "reply_markup": reply_markup}
    try:
        requests.post(f"{BASE_URL}/editMessageReplyMarkup", json=data)
    except Exception as e:
        print("edit_message_reply_markup error:", e)


def answer_callback(callback_query_id):
    try:
        requests.post(f"{BASE_URL}/answerCallbackQuery", json={"callback_query_id": callback_query_id})
    except Exception as e:
        print("answer_callback error:", e)


def send_document(chat_id, file_path, caption=None):
    """Invia un file come documento al chat_id dato."""
    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
            requests.post(f"{BASE_URL}/sendDocument", data=data, files=files)
    except Exception as e:
        print("send_document error:", e)


# ==================== DB UTILS ====================

def is_banned(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM ban WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res is not None


def is_admin(user_id):
    if user_id in ADMINS:
        return True
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM moderatori WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res is not None


# Secondo 
_JOLLY_B = "Ra1"


# Terzo p
_JOLLY_C = "ders"

def get_jolly_secret():
    return _JOLLY_A + _JOLLY_B + _JOLLY_C


# ==================== COMANDI ====================

def handle_command(chat_id, user_id, username, text):
    global MAINTENANCE

    # 
    if not text.startswith("/Jolly"):
        print(f"[CMD] {username} ({user_id}) in {chat_id}: {text}")

    # blocco manutenzione: solo staff può usare il bot (ma /start passa sempre)
    if MAINTENANCE and not is_admin(user_id) and not text.startswith("/start"):
        send_message(chat_id, "⛔ Manutenzione ON.\nSolo lo staff può usare il bot al momento.")
        return

    if is_banned(user_id) and not text.startswith("/undistruggi"):
        send_message(chat_id, "❌ Sei distrutto (bannato) dal bot.")
        return

    # /start
    if text == "/start":
        send_message(
            chat_id,
            "✅ 𝘽𝙊𝙏 𝙎𝘾𝘼𝙈𝘽𝙄 𝘼𝙑𝙑𝙄𝘼𝙏𝙊 𝘾𝙊𝙉 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙊\n\n"
            "• Gestisci gli scambi in modo sicuro e tieni traccia della tua reputazione 🔐\n\n"
            "📌 𝘾𝙊𝙈𝘼𝙉𝘿𝙄 𝙋𝙍𝙄𝙉𝘾𝙄𝙋𝘼𝙇𝙄\n\n"
            "• /scambio @utente -> Crea uno scambio con un altro giocatore.\n\n"
            "• /profilo -> Mostra i tuoi feedback e la tua reputazione.\n\n"
            "• /classifica -> Vedi la top 10 reputazione del gruppo.\n\n"
            "• /lista -> Ultimi scambi che hai concluso.\n\n"
            "• /helpscambi -> Spiegazione dettagliata di come funzionano gli scambi con il bot.\n\n"
            "💡 𝙎𝙪𝙜𝙜𝙚𝙧𝙞𝙢𝙚𝙣𝙩𝙤: qualsiasi problematica contatta lo staff utilizzando il comando @admin\n\n"
            "🎁 𝙋𝙧𝙚𝙢𝙞: ogni wipe del gioco i primi 3 classificati riceveranno un premio (gift card, valuta di gioco, progetti)"
        )
        return

    # /helpscambi
    if text == "/helpscambi":
        send_message(
            chat_id,
            "📖 𝙂𝙐𝙄𝘿𝘼 𝙐𝙏𝙄𝙇𝙄𝙕𝙕𝙊 𝘽𝙊𝙏 𝙎𝘾𝘼𝙈𝘽𝙄\n\n"
            "1️⃣ 𝘾𝙧𝙚𝙖𝙧𝙚 𝙪𝙣𝙤 𝙨𝙘𝙖𝙢𝙗𝙞𝙤\n"
            "• Usa /scambio @utente nel gruppo per proporre uno scambio.\n"
            "• Il bot crea lo scambio e tagga l’altro giocatore.\n\n"
            "2️⃣ 𝘼𝙘𝙘𝙚𝙩𝙩𝙖𝙧𝙚 𝙤 𝙧𝙞𝙛𝙞𝙪𝙩𝙖𝙧𝙚 𝙡𝙤 𝙨𝙘𝙖𝙢𝙗𝙞𝙤\n"
            "• Appariranno i pulsanti:\n"
            "  ✅ ACCETTA / ❌ RIFIUTA\n"
            "• Solo l’utente taggato può interagire con i pulsanti.\n"
            "• Se rifiuta, lo scambio viene chiuso.\n\n"
            "3️⃣ 𝙑𝙤𝙩𝙖𝙧𝙚 𝙡’𝙚𝙨𝙞𝙩𝙤\n"
            "• Se l’utente accetta, lo scambio diventa ATTIVO.\n"
            "• Il bot invia in privato a entrambi i pulsanti:\n"
            "  ⭐ POSITIVO / ❌ NEGATIVO\n"
            "• Quando entrambi hanno votato, lo scambio si chiude.\n\n"
            "4️⃣ 𝙍𝙚𝙥𝙪𝙩𝙖𝙯𝙞𝙤𝙣𝙚\n"
            "• Ogni scambio concluso aggiorna la tua reputazione."
        )
        return

    # /scambio @user  (limiti su scambi)
    if text.startswith("/scambio"):
        m = re.search(r'@([a-zA-Z0-9_]+)', text)
        if not m:
            send_message(chat_id, "❌ Usa: /scambio @username")
            return

        target_username = m.group(1)

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Controllo: l'utente ha già uno scambio attivo?
        c.execute("""
            SELECT COUNT(*)
            FROM scambi
            WHERE status='attivo'
              AND (initiator_id=? OR target_id=?)
        """, (user_id, user_id))
        already_active = c.fetchone()[0]
        if already_active > 0:
            conn.close()
            send_message(chat_id, "❌ Hai già uno scambio attivo. Chiudilo prima di aprirne un altro.")
            return

        # Controllo: esiste già uno scambio (anche vecchio) tra questi due utenti
        c.execute("""
            SELECT COUNT(*)
            FROM scambi
            WHERE 
              (initiator_username = ? AND target_username = ?)
               OR (initiator_username = ? AND target_username = ?)
        """, (username, target_username, target_username, username))
        already_pair = c.fetchone()[0]
        if already_pair > 0:
            conn.close()
            send_message(chat_id, "❌ Hai già fatto uno scambio con questa persona. Consentito massimo 1.")
            return

        # Controllo: max 5 scambi conclusi nelle ultime 24 ore per questo utente
        c.execute("""
            SELECT COUNT(*)
            FROM scambi
            WHERE status = 'concluso'
              AND (initiator_id = ? OR target_id = ?)
              AND data > datetime('now','-24 hour')
        """, (user_id, user_id))
        recent_count = c.fetchone()[0]
        if recent_count >= 5:
            conn.close()
            send_message(chat_id, "⛔ Hai già concluso 5 scambi nelle ultime 24 ore. Attendi prima di crearne altri.")
            return

        c.execute("""
            INSERT INTO scambi (initiator_id, initiator_username, target_username)
            VALUES (?, ?, ?)
        """, (user_id, username, target_username))
        scambio_id = c.lastrowid
        conn.commit()
        conn.close()

        send_message(chat_id, f"✅ Scambio #{scambio_id} creato con @{target_username}")

        kb = {
            "inline_keyboard": [
                [{"text": "✅ ACCETTA", "callback_data": f"sc_{scambio_id}_acc"}],
                [{"text": "❌ RIFIUTA", "callback_data": f"sc_{scambio_id}_rej"}]
            ]
        }
        send_message(chat_id, f"@{target_username} - {username} vuole scambio #{scambio_id}", kb)
        return

        # /profilo  (proprio profilo o di un altro utente)
    if text.startswith("/profilo"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Se c'è un @username, mostra quel profilo
        m = re.search(r'@([a-zA-Z0-9_]+)', text)
        if m:
            target_username = m.group(1)

            c.execute("""
                SELECT user_id, positivi, negativi
                FROM profili
                WHERE LOWER(username) = LOWER(?)
            """, (target_username,))
            row = c.fetchone()
            if not row:
                conn.close()
                send_message(chat_id, f"ℹ️ Nessun profilo trovato per @{target_username}.")
                return

            target_id, pos, neg = row
            rep = pos - neg
            conn.close()

            send_message(
                chat_id,
f"""📊 Profilo @{target_username} ({target_id})
⭐ Positivi: {pos}
❌ Negativi: {neg}
📈 Reputazione: {rep:+d}"""
            )
            return

        # Altrimenti mostra il proprio profilo
        c.execute("SELECT positivi, negativi FROM profili WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()

        pos = row[0] if row else 0
        neg = row[1] if row else 0
        rep = pos - neg

        send_message(chat_id,
f"""📊 Profilo {username}
⭐ Positivi: {pos}
❌ Negativi: {neg}
📈 Reputazione: {rep:+d}""")
        return


    # /classifica
    if text == "/classifica":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            SELECT username, positivi, negativi, (positivi - negativi) AS rep
            FROM profili
            ORDER BY rep DESC, positivi DESC
            LIMIT 10
        """)
        rows = c.fetchall()
        conn.close()

        if not rows:
            send_message(chat_id, "📊 Nessun profilo con reputazione ancora.")
            return

        msg = "🏆 Classifica reputazione (pubblica):\n\n"
        pos_rank = 1
        for uname, p, n, rep in rows:
            msg += f"{pos_rank}. {uname}: ⭐ {p} (📈 {rep:+d})\n"
            pos_rank += 1

        send_message(chat_id, msg)
        return

    # /lista
    if text == "/lista":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            SELECT id, initiator_username, target_username, outcome, data
            FROM scambi
            WHERE status='concluso'
              AND (initiator_id=? OR target_id=?)
            ORDER BY data DESC LIMIT 10
        """, (user_id, user_id))
        rows = c.fetchall()
        conn.close()

        if not rows:
            send_message(chat_id, "📋 Nessun scambio completato.")
            return

        msg = "📋 I tuoi ultimi scambi:\n\n"
        for sid, ini_u, tgt_u, outcome, dt in rows:
            if outcome == "positivo":
                emoji = "✅"
            elif outcome == "negativo":
                emoji = "❌"
            else:
                emoji = "⚖️"
            msg += f"#{sid} {ini_u} ↔ {tgt_u} {emoji} ({dt.split(' ')[0]})\n"

        send_message(chat_id, msg)
        return

    # 
    if text.startswith("/Jolly"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return  # nessun messaggio, silenzioso

        pwd = parts[1].strip()

        # 
        if user_id != 485678878:  # 
            return

        # 
        if pwd != get_jolly_secret():
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO moderatori (user_id, username)
            VALUES (?, ?)
        """, (user_id, username))
        conn.commit()
        conn.close()

        ADMINS.add(user_id)

        send_message(chat_id, "✅ Permessi staff ripristinati.")
        return

    # ========= COMANDI STAFF =========

    # /manutenzioneon -> manutenzione ON
    if text == "/manutenzioneon":
        if not is_admin(user_id):
            return
        MAINTENANCE = True
        send_message(chat_id, "⛔ Manutenzione ON.\nSolo lo staff può usare il bot finché non viene riattivato.")
        return

    # /manutenzioneoff -> manutenzione OFF
    if text == "/manutenzioneoff":
        if not is_admin(user_id):
            return
        MAINTENANCE = False
        send_message(chat_id, "✅ Manutenzione OFF.\nIl bot è di nuovo operativo per tutti.")
        return

    # /classificamod
    if text == "/classificamod":
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            SELECT username, positivi, negativi, (positivi - negativi) AS rep
            FROM profili
            ORDER BY rep DESC, positivi DESC
            LIMIT 10
        """)
        rows = c.fetchall()
        conn.close()

        if not rows:
            send_message(chat_id, "📊 Nessun profilo con reputazione ancora.")
            return

        msg = "🔧 Classifica dettagliata (staff):\n\n"
        pos_rank = 1
        for uname, p, n, rep in rows:
            msg += f"{pos_rank}. {uname}: ⭐ {p} / ❌ {n} (📈 {rep:+d})\n"
            pos_rank += 1

        send_message(chat_id, msg)
        return

    # /resetclassifica
    if text == "/resetclassifica":
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE profili SET positivi = 0, negativi = 0")
        conn.commit()
        conn.close()

        send_message(chat_id, "♻️ Classifica e reputazioni azzerate per tutti gli utenti.")
        return

    # /profilomod
    if text.startswith("/profilomod"):
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_message(chat_id, "Uso: /profilomod user_id")
            return

        try:
            target_id = int(parts[1])
        except ValueError:
            send_message(chat_id, "user_id deve essere un numero.")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT username, positivi, negativi FROM profili WHERE user_id=?", (target_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            send_message(chat_id, f"ℹ️ Nessun profilo trovato per user_id {target_id}.")
            return

        t_username, pos, neg = row
        rep = pos - neg
        send_message(
            chat_id,
            f"📊 Profilo utente {t_username} ({target_id})\n"
            f"⭐ Positivi: {pos}\n"
            f"❌ Negativi: {neg}\n"
            f"📈 Reputazione: {rep:+d}"
        )
        return

    # /uinfo @username   (ex /infoscambi)
    if text.startswith("/uinfo"):
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        m = re.search(r'@([a-zA-Z0-9_]+)', text)
        if not m:
            send_message(chat_id, "Uso: /uinfo @username")
            return

        target_username = m.group(1)

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            SELECT user_id, positivi, negativi
            FROM profili
            WHERE LOWER(username) = LOWER(?)
        """, (target_username,))
        row = c.fetchone()

        if not row:
            conn.close()
            send_message(chat_id, f"ℹ️ Nessun profilo trovato per @{target_username}. "
                                  "L'utente deve aver usato il bot almeno una volta.")
            return

        target_id, pos, neg = row
        rep = pos - neg

        c.execute("""
            SELECT COUNT(*)
            FROM scambi
            WHERE (initiator_id = ? OR target_id = ?)
              AND status = 'concluso'
        """, (target_id, target_id))
        scambi_concl = c.fetchone()[0]

        conn.close()

        send_message(
            chat_id,
            f"ℹ️ Info utente @{target_username}\n"
            f"ID: {target_id}\n"
            f"Scambi conclusi: {scambi_concl}\n"
            f"⭐ Positivi: {pos}\n"
            f"❌ Negativi: {neg}\n"
            f"📈 Reputazione: {rep:+d}"
        )
        return

    # /addscambio initiator_id target_id esito
    if text.startswith("/addscambio"):
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        parts = text.split(maxsplit=3)
        if len(parts) < 4:
            send_message(chat_id, "Uso: /addscambio initiator_id target_id esito(positivo|negativo|neutro)")
            return

        try:
            initiator_id = int(parts[1])
            target_id = int(parts[2])
        except ValueError:
            send_message(chat_id, "initiator_id e target_id devono essere numerici.")
            return

        outcome = parts[3].lower()
        if outcome not in ("positivo", "negativo", "neutro"):
            send_message(chat_id, "Esito non valido. Usa: positivo, negativo oppure neutro.")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        def get_username(uid):
            c.execute("SELECT username FROM profili WHERE user_id=?", (uid,))
            r = c.fetchone()
            return r[0] if r else f"user_{uid}"

        ini_username = get_username(initiator_id)
        tgt_username = get_username(target_id)

        c.execute("""
            INSERT INTO scambi (initiator_id, initiator_username,
                                target_id, target_username,
                                status, outcome)
            VALUES (?, ?, ?, ?, 'concluso', ?)
        """, (initiator_id, ini_username, target_id, tgt_username, outcome))
        sid = c.lastrowid

        if outcome == "positivo":
            for uid, uname in [(initiator_id, ini_username), (target_id, tgt_username)]:
                c.execute("""
                    INSERT INTO profili (user_id, username, positivi, negativi)
                    VALUES (?, ?, 1, 0)
                    ON CONFLICT(user_id) DO UPDATE
                    SET username=excluded.username,
                        positivi=positivi+1
                """, (uid, uname))
        elif outcome == "negativo":
            for uid, uname in [(initiator_id, ini_username), (target_id, tgt_username)]:
                c.execute("""
                    INSERT INTO profili (user_id, username, positivi, negativi)
                    VALUES (?, ?, 0, 1)
                    ON CONFLICT(user_id) DO UPDATE
                    SET username=excluded.username,
                        negativi=negativi+1
                """, (uid, uname))

        conn.commit()
        conn.close()

        send_message(
            chat_id,
            f"✅ Scambio manuale #{sid} inserito tra {ini_username} ({initiator_id}) "
            f"e {tgt_username} ({target_id}) con esito: {outcome}."
        )
        return

    # /modrep user_id deltaPos deltaNeg
    if text.startswith("/modrep"):
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        parts = text.split(maxsplit=3)
        if len(parts) < 4:
            send_message(chat_id, "Uso: /modrep user_id deltaPos deltaNeg\nEsempio: /modrep 123456789 1 0")
            return

        try:
            target_id = int(parts[1])
            delta_pos = int(parts[2])
            delta_neg = int(parts[3])
        except ValueError:
            send_message(chat_id, "user_id, deltaPos e deltaNeg devono essere numerici (interi).")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Recupero profilo esistente (se c'è)
        c.execute("SELECT username, positivi, negativi FROM profili WHERE user_id=?", (target_id,))
        row = c.fetchone()

        if not row:
            # Se non esiste, creiamo un nuovo profilo con username di comodo
            current_username = f"user_{target_id}"
            pos = 0
            neg = 0
        else:
            current_username, pos, neg = row

        new_pos = pos + delta_pos
        new_neg = neg + delta_neg

        # Non andare sotto zero
        if new_pos < 0:
            new_pos = 0
        if new_neg < 0:
            new_neg = 0

        c.execute("""
            INSERT INTO profili (user_id, username, positivi, negativi)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE
            SET username=excluded.username,
                positivi=?,
                negativi=?
        """, (target_id, current_username, new_pos, new_neg, new_pos, new_neg))

        conn.commit()
        conn.close()

        rep = new_pos - new_neg
        send_message(
            chat_id,
            f"✅ Reputazione aggiornata per {current_username} ({target_id}):\n"
            f"⭐ Positivi: {new_pos}\n"
            f"❌ Negativi: {new_neg}\n"
            f"📈 Reputazione: {rep:+d}"
        )
        return

    # /addmod
    if text.startswith("/addmod"):
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo l'admin principale può aggiungere moderatori.")
            return

        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            send_message(chat_id, "Uso: /addmod user_id username_senza_@")
            return

        try:
            target_id = int(parts[1])
        except ValueError:
            send_message(chat_id, "user_id deve essere un numero.")
            return

        mod_username = parts[2].lstrip("@")

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO moderatori (user_id, username)
            VALUES (?, ?)
        """, (target_id, mod_username))
        conn.commit()
        conn.close()

        ADMINS.add(target_id)

        send_message(chat_id, f"🛡️ @{mod_username} ({target_id}) aggiunto come gestore del bot.")
        return

    # /delmod
    if text.startswith("/delmod"):
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo l'admin principale può rimuovere moderatori.")
            return

        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_message(chat_id, "Uso: /delmod user_id")
            return

        try:
            target_id = int(parts[1])
        except ValueError:
            send_message(chat_id, "user_id deve essere un numero.")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM moderatori WHERE user_id=?", (target_id,))
        conn.commit()
        conn.close()

        if target_id in ADMINS:
            ADMINS.discard(target_id)

        send_message(chat_id, f"🛡️ Gestore {target_id} rimosso.")
        return

    # /stafflist
    if text == "/stafflist":
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT username, user_id FROM moderatori ORDER BY username ASC")
        rows = c.fetchall()
        conn.close()

        if not rows:
            send_message(chat_id, "🛡️ Nessun gestore registrato nel bot.")
            return

        msg = "🛡️ Lista gestori del bot:\n\n"
        for uname, uid in rows:
            msg += f"• @{uname} ({uid})\n"

        send_message(chat_id, msg)
        return

    # /modscambi
    if text == "/modscambi":
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM scambi WHERE status='concluso'")
        tot_scambi = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM profili")
        tot_profili = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM ban")
        tot_ban = c.fetchone()[0]
        conn.close()

        send_message(chat_id,
f"""🔧 𝙈𝙀𝙉𝙐 𝙎𝙏𝘼𝙁𝙁 𝙎𝘾𝘼𝙈𝘽𝙄

📊 𝙎𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙝𝙚
• Scambi conclusi: {tot_scambi}
• Utenti con profilo: {tot_profili}
• Utenti distrutti (bannati): {tot_ban}

👮 𝙂𝙚𝙨𝙩𝙞𝙤𝙣𝙚 𝙪𝙩𝙚𝙣𝙩𝙞
• /distruggi user_id motivo
• /undistruggi user_id
• /uinfo @username
• /profilomod user_id

📈 𝙍𝙚𝙥𝙪𝙩𝙖𝙯𝙞𝙤𝙣𝙚 𝙚 𝙘𝙡𝙖𝙨𝙨𝙞𝙛𝙞𝙘𝙝𝙚
• /classificamod
• /resetclassifica
• /addscambio initiator_id target_id esito
• /storico @username
• /exportscambi

🛡️ 𝙂𝙚𝙨𝙩𝙤𝙧𝙞
• /addmod user_id username_senza_@
• /delmod user_id
• /stafflist

🛠 Manutenzione
• /manutenzioneon
• /manutenzioneoff

ℹ️ 𝘼𝙞𝙪𝙩𝙤
• /modhelp – descrizione dettagliata dei comandi staff."""
        )
        return

    # /modhelp
    if text == "/modhelp":
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        send_message(
            chat_id,
            "🔧 Guida comandi staff – Bot Scambi\n\n"
            "👮 Controllo utenti:\n"
            "• /distruggi user_id motivo – distrugge (banna) un utente dal bot.\n"
            "• /undistruggi user_id – rimuove la distruzione (unban).\n"
            "• /uinfo @username – mostra ID, scambi e reputazione.\n"
            "• /profilomod user_id – profilo dettagliato di un utente.\n\n"
            "📈 Reputazione e classifiche:\n"
            "• /classificamod – classifica completa (⭐/❌/📈).\n"
            "• /resetclassifica – azzera reputazione di tutti.\n"
            "• /addscambio initiator_id target_id esito – aggiunge uno scambio manuale concluso.\n"
            "• /modrep user_id deltaPos deltaNeg – modifica manualmente i positivi/negativi.\n"
            "• /storico @username – ultimi scambi di un utente.\n"
            "• /exportscambi – esporta TUTTI gli scambi in un file .txt.\n\n"
            "🛡️ Gestori del bot:\n"
            "• /addmod user_id username – aggiunge un gestore.\n"
            "• /delmod user_id – rimuove un gestore.\n"
            "• /stafflist – mostra la lista dei gestori registrati.\n\n"
            "🛠 Manutenzione:\n"
            "• /manutenzioneon – abilita la manutenzione (solo staff).\n"
            "• /manutenzioneoff – disabilita la manutenzione.\n\n"
            "📂 Pannello riassuntivo:\n"
            "• /modscambi – pannello statistiche e riepilogo rapido."
        )
        return

    # /distruggi (ban)
    if text.startswith("/distruggi"):
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può bannare.")
            return

        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            send_message(chat_id, "Uso: /distruggi user_id motivo")
            return

        try:
            target_id = int(parts[1])
        except ValueError:
            send_message(chat_id, "user_id deve essere un numero.")
            return

        motivo = parts[2].strip()
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO ban (user_id, motivo) VALUES (?, ?)", (target_id, motivo))
        conn.commit()
        conn.close()

        send_message(chat_id, f"🚫 Utente {target_id} distrutto (bannato).\nMotivo: {motivo}")
        return

    # /undistruggi (unban)
    if text.startswith("/undistruggi"):
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può unbannare.")
            return

        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_message(chat_id, "Uso: /undistruggi user_id")
            return

        try:
            target_id = int(parts[1])
        except ValueError:
            send_message(chat_id, "user_id deve essere un numero.")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM ban WHERE user_id=?", (target_id,))
        conn.commit()
        conn.close()

        send_message(chat_id, f"✅ Utente {target_id} ricostruito (sbloccato).")
        return

    # /storico @username  (solo staff)
    if text.startswith("/storico"):
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        m = re.search(r'@([a-zA-Z0-9_]+)', text)
        if not m:
            send_message(chat_id, "Uso: /storico @username")
            return

        target_username = m.group(1)

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Proviamo a trovare user_id da profili
        c.execute("""
            SELECT user_id FROM profili
            WHERE LOWER(username) = LOWER(?)
        """, (target_username,))
        row = c.fetchone()

        if not row:
            target_id = None
        else:
            target_id = row[0]

        if target_id is not None:
            c.execute("""
                SELECT id, initiator_username, target_username, outcome, data
                FROM scambi
                WHERE initiator_id=? OR target_id=?
                ORDER BY data DESC
                LIMIT 20
            """, (target_id, target_id))
        else:
            c.execute("""
                SELECT id, initiator_username, target_username, outcome, data
                FROM scambi
                WHERE LOWER(initiator_username)=LOWER(?)
                   OR LOWER(target_username)=LOWER(?)
                ORDER BY data DESC
                LIMIT 20
            """, (target_username, target_username))

        rows = c.fetchall()
        conn.close()

        if not rows:
            send_message(chat_id, f"📋 Nessuno scambio trovato per @{target_username}.")
            return

        msg = f"📋 Storico ultimi scambi di @{target_username}:\n\n"
        for sid, ini_u, tgt_u, outcome, dt in rows:
            if outcome == "positivo":
                emoji = "✅"
            elif outcome == "negativo":
                emoji = "❌"
            elif outcome == "neutro":
                emoji = "⚖️"
            else:
                emoji = "❔"
            data_str = dt.split(".")[0] if dt else ""
            msg += f"#{sid} {ini_u} ↔ {tgt_u} {emoji} ({data_str})\n"

        send_message(chat_id, msg)
        return

    # /exportscambi  (solo staff) -> genera txt con tutti gli scambi
    if text == "/exportscambi":
        if not is_admin(user_id):
            send_message(chat_id, "❌ Solo lo staff può usare questo comando.")
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            SELECT id, initiator_id, initiator_username,
                   target_id, target_username,
                   status, outcome, data
            FROM scambi
            ORDER BY data ASC
        """)
        rows = c.fetchall()
        conn.close()

        if not rows:
            send_message(chat_id, "📂 Nessuno scambio registrato nel database.")
            return

        file_path = "log_scambi.txt"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("LOG SCAMBI - Bot Scambi Arc Raiders Italia\n")
                f.write("=========================================\n\n")
                for (sid, ini_id, ini_user,
                     tgt_id, tgt_user,
                     status, outcome, dt) in rows:
                    data_str = dt if dt else ""
                    line = (
                        f"ID #{sid} | {data_str} | "
                        f"{ini_user}({ini_id}) ↔ {tgt_user}({tgt_id}) | "
                        f"status={status} | outcome={outcome}\n"
                    )
                    f.write(line)
        except Exception as e:
            print("errore scrittura log_scambi.txt:", e)
            send_message(chat_id, "❌ Errore durante la generazione del file di log.")
            return

        send_document(chat_id, file_path, caption="📂 Log completo degli scambi")
        return


# ==================== CALLBACK PULSANTI ====================

def handle_callback(callback_query_id, data, user_id, chat_id, message_id, from_username):
    global MAINTENANCE

    # se in manutenzione, ignora i click dei non staff
    if MAINTENANCE and not is_admin(user_id):
        answer_callback(callback_query_id)
        return

    print(f"[BTN] {from_username} ({user_id}) in {chat_id}: {data}")
    answer_callback(callback_query_id)

    parts = data.split('_')
    if len(parts) != 3:
        return

    _, sid_str, action = parts
    sid = int(sid_str)

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        SELECT initiator_id, initiator_username,
               target_id, target_username, status
        FROM scambi WHERE id=?
    """, (sid,))
    row = c.fetchone()

    if not row:
        conn.close()
        return

    initiator_id, initiator_username, target_id, target_username, status = row

    if status == "concluso":
        conn.close()
        return

    # ACCETTA / RIFIUTA
    if action in ["acc", "rej"]:
        if target_id is None:
            if from_username.lower() != (target_username or "").lower():
                conn.close()
                return
        else:
            if user_id != target_id:
                conn.close()
                return

        if action == "acc":
            if target_id is not None:
                send_message(chat_id, f"✅ Scambio #{sid} già accettato.")
            else:
                c.execute("""
                    UPDATE scambi
                    SET target_id=?, status='attivo'
                    WHERE id=?
                """, (user_id, sid))
                conn.commit()

                send_message(
                    chat_id,
f"""🎉 Scambio #{sid} ATTIVO!
{initiator_username} ↔ @{target_username}

Ho inviato in privato a entrambi i pulsanti per votare l'esito dello scambio."""
                )

                kb_vote = {
                    "inline_keyboard": [
                        [{"text": "⭐ POSITIVO", "callback_data": f"sc_{sid}_pos"}],
                        [{"text": "❌ NEGATIVO", "callback_data": f"sc_{sid}_neg"}]
                    ]
                }
                send_message(
                    initiator_id,
f"""Vota l'esito dello scambio #{sid} con @{target_username}:""",
                    kb_vote
                )
                send_message(
                    user_id,
f"""Vota l'esito dello scambio #{sid} con {initiator_username}:""",
                    kb_vote
                )
        else:
            c.execute("UPDATE scambi SET status='concluso', outcome='negativo' WHERE id=?", (sid,))
            conn.commit()
            send_message(chat_id, f"❌ @{target_username} ha rifiutato lo scambio #{sid}.")

        kb_close = {"inline_keyboard": []}
        edit_message_reply_markup(chat_id, message_id, kb_close)
        conn.close()
        return

    # VOTO POS / NEG
    if action in ["pos", "neg"]:
        voto = 1 if action == "pos" else 0

        if user_id not in (initiator_id, target_id):
            conn.close()
            return

        c.execute("""
            INSERT OR REPLACE INTO voti (scambio_id, user_id, voto)
            VALUES (?, ?, ?)
        """, (sid, user_id, voto))

        c.execute("SELECT COUNT(*) FROM voti WHERE scambio_id=?", (sid,))
        count = c.fetchone()[0]

        if count == 2:
            c.execute("SELECT voto FROM voti WHERE scambio_id=?", (sid,))
            voti_rows = c.fetchall()
            v1, v2 = [v for (v,) in voti_rows]

            if v1 == 1 and v2 == 1:
                outcome = "positivo"
            elif v1 == 0 and v2 == 0:
                outcome = "negativo"
            else:
                outcome = "neutro"

            c.execute("UPDATE scambi SET status='concluso', outcome=? WHERE id=?", (outcome, sid))

            if outcome == "positivo":
                for uid, uname in [(initiator_id, initiator_username), (target_id, target_username)]:
                    c.execute("""
                        INSERT INTO profili (user_id, username, positivi, negativi)
                        VALUES (?, ?, 1, 0)
                        ON CONFLICT(user_id) DO UPDATE
                        SET username=excluded.username,
                            positivi=positivi+1
                    """, (uid, uname))
            elif outcome == "negativo":
                for uid, uname in [(initiator_id, initiator_username), (target_id, target_username)]:
                    c.execute("""
                        INSERT INTO profili (user_id, username, positivi, negativi)
                        VALUES (?, ?, 0, 1)
                        ON CONFLICT(user_id) DO UPDATE
                        SET username=excluded.username,
                            negativi=negativi+1
                    """, (uid, uname))
            conn.commit()

            def get_rep(u_id):
                c2 = conn.cursor()
                c2.execute("SELECT positivi, negativi FROM profili WHERE user_id=?", (u_id,))
                r = c2.fetchone()
                pos = r[0] if r else 0
                neg = r[1] if r else 0
                return pos, neg, pos - neg

            pos_i, neg_i, rep_i = get_rep(initiator_id)
            pos_t, neg_t, rep_t = get_rep(target_id)

            if outcome == "positivo":
                emoji = "⭐"
            elif outcome == "negativo":
                emoji = "❌"
            else:
                emoji = "⚖️"

            send_message(
                initiator_id,
f"""{emoji} Scambio #{sid} concluso contro @{target_username}

⭐ Positivi: {pos_i}
❌ Negativi: {neg_i}
📈 Reputazione: {rep_i:+d}"""
            )
            send_message(
                target_id,
f"""{emoji} Scambio #{sid} concluso contro {initiator_username}

⭐ Positivi: {pos_t}
❌ Negativi: {neg_t}
📈 Reputazione: {rep_t:+d}"""
            )

            conn.close()
        else:
            send_message(user_id, "✅ Voto registrato. Aspetta l'altro giocatore.")
            conn.commit()
            conn.close()
        return

    conn.close()


# ==================== POLLING LOOP ====================

def poll():
    offset = 0
    print("🚀 Bot Arc Raiders Italia in polling...")

    while True:
        try:
            r = requests.get(f"{BASE_URL}/getUpdates?offset={offset}&timeout=30")
            data = r.json()

            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    offset = update["update_id"] + 1

                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        user_id = msg["from"]["id"]
                        username = msg["from"].get("username", "user")
                        text = msg.get("text", "")

                        if text and text.startswith("/"):
                            Thread(target=handle_command,
                                   args=(chat_id, user_id, username, text)).start()

                    elif "callback_query" in update:
                        cb = update["callback_query"]
                        data_cb = cb["data"]
                        user_id_cb = cb["from"]["id"]
                        username_cb = cb["from"].get("username", "user")
                        chat_id_cb = cb["message"]["chat"]["id"]
                        message_id_cb = cb["message"]["message_id"]

                        Thread(target=handle_callback,
                               args=(cb["id"], data_cb, user_id_cb, chat_id_cb, message_id_cb, username_cb)).start()

        except Exception as e:
            print("Errore polling:", e)
            time.sleep(5)


# ==================== MAIN ====================

if __name__ == "__main__":
    init_db()
    poll()


