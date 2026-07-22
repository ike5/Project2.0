import sys
import os
import unicodedata
import re
import sqlite3
import hashlib
from datetime import datetime, timezone


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "progress.db")


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db():
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id TEXT NOT NULL,
            question_hash TEXT NOT NULL,
            question_type TEXT NOT NULL CHECK(question_type IN ('translation', 'mc')),
            question_text TEXT NOT NULL,
            attempt_number INTEGER NOT NULL,
            user_answer TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            needed_retry INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            total_questions INTEGER,
            first_try_correct INTEGER,
            after_retry_correct INTEGER,
            final_incorrect INTEGER
        );

        CREATE INDEX IF NOT EXISTS idx_attempts_lesson ON attempts(lesson_id);
        CREATE INDEX IF NOT EXISTS idx_attempts_hash ON attempts(question_hash);
        CREATE INDEX IF NOT EXISTS idx_attempts_lesson_hash ON attempts(lesson_id, question_hash);
        CREATE INDEX IF NOT EXISTS idx_sessions_lesson ON sessions(lesson_id);
    """)
    conn.commit()
    conn.close()


def normalize(text):
    text = text.strip().lower()
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[¡!¿?.,;:]", "", text)
    text = " ".join(text.split())
    return text


def matches(answer, accepted):
    n_answer = normalize(answer)
    if isinstance(accepted, str):
        accepted = [accepted]
    for a in accepted:
        if normalize(a) == n_answer:
            return True
    return False


def _question_hash(question_text):
    return hashlib.sha256(question_text.encode("utf-8")).hexdigest()[:16]


def _extract_lesson_id(title):
    match = re.match(r"(?:Lecci[oó]n|Lesson)\s*(\d+)", title, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        return f"lesson_{num:02d}"
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower().strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug[:50]


def _record_attempt(lesson_id, question_hash, question_type, question_text,
                    attempt_number, user_answer, correct_answer,
                    is_correct, needed_retry):
    conn = _get_db()
    conn.execute(
        """INSERT INTO attempts
           (lesson_id, question_hash, question_type, question_text,
            attempt_number, user_answer, correct_answer, is_correct,
            needed_retry, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (lesson_id, question_hash, question_type, question_text,
         attempt_number, user_answer, correct_answer, int(is_correct),
         int(needed_retry), datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()


def _start_session(lesson_id):
    conn = _get_db()
    cursor = conn.execute(
        """INSERT INTO sessions (lesson_id, started_at, finished_at,
           total_questions, first_try_correct, after_retry_correct, final_incorrect)
           VALUES (?, ?, NULL, 0, 0, 0, 0)""",
        (lesson_id, datetime.now(timezone.utc).isoformat())
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def _finish_session(session_id, total, first_try, after_retry, final_incorrect):
    conn = _get_db()
    conn.execute(
        """UPDATE sessions SET
           finished_at = ?, total_questions = ?,
           first_try_correct = ?, after_retry_correct = ?,
           final_incorrect = ?
           WHERE id = ?""",
        (datetime.now(timezone.utc).isoformat(), total,
         first_try, after_retry, final_incorrect, session_id)
    )
    conn.commit()
    conn.close()


def run_exercises(exercises, title=""):
    _init_db()
    lesson_id = _extract_lesson_id(title)

    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print()
    print("Type your answer and press ENTER. Press 'q' to quit early.")
    print("Minor accent/punctuation differences are forgiven.")
    print("Wrong? You get one retry. Miss twice and the answer is revealed.\n")

    first_try_correct = 0
    after_retry_correct = 0
    final_incorrect = 0
    total = 0
    skipped = 0
    session_id = _start_session(lesson_id)

    for i, ex in enumerate(exercises, 1):
        q = ex.get("question", "")
        hint = ex.get("hint", "")
        accepted = ex.get("answer", [])
        explanation = ex.get("explanation", "")
        context = ex.get("context", "")

        if isinstance(accepted, str):
            accepted = [accepted]

        total += 1
        q_hash = _question_hash(q)

        print(f"--- Question {i}/{len(exercises)} ---")
        if context:
            print(f"  Context: {context}")
        print(f"  {q}")
        if hint:
            print(f"  Hint: {hint}")
        print()

        got_it = False
        needed_retry = False
        display_answers = accepted if len(accepted) <= 3 else accepted[:3]

        for attempt in range(1, 3):
            try:
                user_input = input(f"  Your answer (attempt {attempt}/2): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nSession ended early.")
                _finish_session(session_id, total - 1, first_try_correct,
                                after_retry_correct, final_incorrect)
                _print_results(first_try_correct, after_retry_correct,
                               final_incorrect, total - 1, skipped + len(exercises) - i)
                return

            if user_input.lower() == "q":
                skipped = len(exercises) - i
                print("\nSession ended early.")
                _finish_session(session_id, total - 1, first_try_correct,
                                after_retry_correct, final_incorrect)
                _print_results(first_try_correct, after_retry_correct,
                               final_incorrect, total - 1, skipped)
                return

            if matches(user_input, accepted):
                got_it = True
                if attempt == 1:
                    first_try_correct += 1
                    print(f"  \u2705 Correct on the first try!")
                else:
                    after_retry_correct += 1
                    print(f"  \u2705 Correct on retry!")
                _record_attempt(lesson_id, q_hash, "translation", q,
                                attempt, user_input, display_answers[0],
                                True, needed_retry)
                break
            else:
                if attempt == 1:
                    needed_retry = True
                    print(f"  \u274c Not quite. Try once more!")
                    print()
                else:
                    print(f"  \u274c Still not quite. The answer: {' / '.join(display_answers)}")
                    final_incorrect += 1
                    _record_attempt(lesson_id, q_hash, "translation", q,
                                    attempt, user_input, display_answers[0],
                                    False, True)

        if not got_it:
            pass

        if explanation:
            print(f"  \U0001f4d6 {explanation}")

        print()

    _finish_session(session_id, total, first_try_correct,
                     after_retry_correct, final_incorrect)
    _print_results(first_try_correct, after_retry_correct,
                    final_incorrect, total, skipped)


def choose_translation(pairs, title=""):
    _init_db()
    lesson_id = _extract_lesson_id(title)

    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print()
    print("Choose the best translation. Press 'q' to quit early.\n")

    first_try_correct = 0
    after_retry_correct = 0
    final_incorrect = 0
    total = 0
    skipped = 0
    session_id = _start_session(lesson_id)

    for i, (english, spanish_options, correct_idx, explanation) in enumerate(pairs, 1):
        total += 1
        q_text = english
        q_hash = _question_hash(q_text)
        correct_answer = spanish_options[correct_idx - 1]

        print(f"--- Question {i}/{len(pairs)} ---")
        print(f"  Which is the best Mexican Spanish translation?")
        print(f"  \"{english}\"")
        print()
        for j, opt in enumerate(spanish_options, 1):
            print(f"    {j}) {opt}")
        print()

        got_it = False
        needed_retry = False

        for attempt in range(1, 3):
            try:
                choice = input(f"  Your choice (1-{len(spanish_options)}, or 'q' to quit) [{attempt}/2]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nSession ended early.")
                _finish_session(session_id, total - 1, first_try_correct,
                                after_retry_correct, final_incorrect)
                _print_results(first_try_correct, after_retry_correct,
                               final_incorrect, total - 1, skipped + len(pairs) - i)
                return

            if choice.lower() == "q":
                skipped = len(pairs) - i
                print("\nSession ended early.")
                _finish_session(session_id, total - 1, first_try_correct,
                                after_retry_correct, final_incorrect)
                _print_results(first_try_correct, after_retry_correct,
                               final_incorrect, total - 1, skipped)
                return

            try:
                choice_num = int(choice)
            except ValueError:
                print("  Invalid input. Try again.\n")
                continue

            if choice_num == correct_idx:
                got_it = True
                if attempt == 1:
                    first_try_correct += 1
                    print(f"  \u2705 Correct on the first try!")
                else:
                    after_retry_correct += 1
                    print(f"  \u2705 Correct on retry!")
                _record_attempt(lesson_id, q_hash, "mc", q_text,
                                attempt, choice, correct_answer,
                                True, needed_retry)
                break
            else:
                if attempt == 1:
                    needed_retry = True
                    print(f"  \u274c Not quite. Try once more!")
                    print()
                else:
                    print(f"  \u274c The best answer was {correct_idx}) {correct_answer}")
                    final_incorrect += 1
                    _record_attempt(lesson_id, q_hash, "mc", q_text,
                                    attempt, choice, correct_answer,
                                    False, True)

        if explanation:
            print(f"  \U0001f4d6 {explanation}")
        print()

    _finish_session(session_id, total, first_try_correct,
                     after_retry_correct, final_incorrect)
    _print_results(first_try_correct, after_retry_correct,
                    final_incorrect, total, skipped)


def _print_results(first_try, after_retry, final_incorrect, total, skipped):
    correct_total = first_try + after_retry
    pct = (correct_total / total * 100) if total > 0 else 0
    first_pct = (first_try / total * 100) if total > 0 else 0
    retry_pct = (after_retry / total * 100) if total > 0 else 0
    miss_pct = (final_incorrect / total * 100) if total > 0 else 0

    print()
    print("=" * 60)
    print(f"  RESULTS: {correct_total}/{total} correct")
    if skipped:
        print(f"  ({skipped} skipped)")
    print(f"  Overall score: {pct:.0f}%")
    print()
    print(f"  First try correct:    {first_try:>3}  ({first_pct:.0f}%)")
    print(f"  Correct after retry:   {after_retry:>3}  ({retry_pct:.0f}%)")
    print(f"  Still incorrect:       {final_incorrect:>3}  ({miss_pct:.0f}%)")
    print("=" * 60)

    db_display = os.path.relpath(DB_PATH, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    print(f"\n  Progress saved to {db_display}")
    print(f"  Run 'python3 code/analytics.py' to see your learning stats.\n")