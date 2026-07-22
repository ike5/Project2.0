import sqlite3
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import math

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "progress.db")

LESSON_NAMES = {
    "lesson_01": "Present Subjunctive",
    "lesson_02": "Imperfect Subjunctive & Conditional",
    "lesson_03": "Se lo / Se la (Double Pronouns)",
    "lesson_04": "Object Reference",
    "lesson_05": "Irregular Verbs (Stem-Changing)",
    "lesson_06": "Irregular Verbs (Advanced & Idioms)",
    "lesson_07": "Subjunctive in Clauses",
    "lesson_08": "Perfect Tenses",
    "lesson_09": "Mexican Dialect & Culture",
    "lesson_10": "Capstone (Mixed)",
}


def _get_db():
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _lesson_display(lesson_id):
    return LESSON_NAMES.get(lesson_id, lesson_id)


def _pct(n, total):
    if total == 0:
        return "N/A"
    return f"{n / total * 100:.1f}%"


def _ci95(p, n):
    if n == 0:
        return "N/A"
    z = 1.96
    se = math.sqrt(p * (1 - p) / n) if 0 < p < 1 else 0
    lo = max(0, p - z * se)
    hi = min(1, p + z * se)
    return f"[{lo * 100:.1f}%, {hi * 100:.1f}%]"


def _streak(attempts_rows):
    streak = 0
    for row in reversed(attempts_rows):
        if row["is_correct"] and row["attempt_number"] == 1:
            streak += 1
        else:
            break
    return streak


def overview(conn):
    print()
    print("=" * 70)
    print("  OVERALL PROGRESS")
    print("=" * 70)

    total_attempts = conn.execute("SELECT COUNT(*) as c FROM attempts").fetchone()["c"]
    total_sessions = conn.execute("SELECT COUNT(*) as c FROM sessions WHERE finished_at IS NOT NULL").fetchone()["c"]

    if total_attempts == 0:
        print("\n  No attempts recorded yet. Start a lesson first!\n")
        return False

    first_try = conn.execute(
        "SELECT COUNT(*) as c FROM attempts WHERE is_correct = 1 AND attempt_number = 1"
    ).fetchone()["c"]

    retry_correct = conn.execute(
        "SELECT COUNT(*) as c FROM attempts WHERE is_correct = 1 AND attempt_number > 1 AND needed_retry = 1"
    ).fetchone()["c"]

    final_wrong = conn.execute(
        """SELECT COUNT(DISTINCT question_hash) as c FROM attempts a1
           WHERE a1.is_correct = 0 AND a1.attempt_number = 2
           AND NOT EXISTS (
               SELECT 1 FROM attempts a2
               WHERE a2.question_hash = a1.question_hash
               AND a2.is_correct = 1 AND a2.attempt_number = 1
           )"""
    ).fetchone()["c"]

    unique_questions = conn.execute("SELECT COUNT(DISTINCT question_hash) as c FROM attempts").fetchone()["c"]
    unique_correct_first = conn.execute(
        """SELECT COUNT(DISTINCT question_hash) as c FROM attempts
           WHERE is_correct = 1 AND attempt_number = 1"""
    ).fetchone()["c"]

    print()
    print(f"  Total sessions:              {total_sessions}")
    print(f"  Total question attempts:      {total_attempts}")
    print(f"  Unique questions attempted:    {unique_questions}")
    print()
    print(f"  First-try accuracy:           {first_try}/{unique_questions}  ({_pct(unique_correct_first, unique_questions)})")

    p = unique_correct_first / unique_questions if unique_questions > 0 else 0
    ci = _ci95(p, unique_questions)
    print(f"  95% CI for first-try rate:     {ci}")

    print(f"  Correct after retry:          {retry_correct}")
    print(f"  Never correct (2 misses):      {final_wrong}")
    print()

    first_attempt_date = conn.execute("SELECT MIN(timestamp) as t FROM attempts").fetchone()["t"]
    last_attempt_date = conn.execute("SELECT MAX(timestamp) as t FROM attempts").fetchone()["t"]
    print(f"  First session:  {first_attempt_date[:10] if first_attempt_date else 'N/A'}")
    print(f"  Last session:    {last_attempt_date[:10] if last_attempt_date else 'N/A'}")

    return True


def per_lesson(conn):
    print()
    print("=" * 70)
    print("  PER-LESSON BREAKDOWN")
    print("=" * 70)
    print()

    lessons = conn.execute(
        "SELECT DISTINCT lesson_id FROM attempts ORDER BY lesson_id"
    ).fetchall()

    for row in lessons:
        lid = row["lesson_id"]
        name = _lesson_display(lid)

        unique_q = conn.execute(
            "SELECT COUNT(DISTINCT question_hash) as c FROM attempts WHERE lesson_id = ?",
            (lid,)
        ).fetchone()["c"]

        first_try = conn.execute(
            "SELECT COUNT(DISTINCT question_hash) as c FROM attempts WHERE lesson_id = ? AND is_correct = 1 AND attempt_number = 1",
            (lid,)
        ).fetchone()["c"]

        retry_ok = conn.execute(
            """SELECT COUNT(DISTINCT question_hash) as c FROM attempts
               WHERE lesson_id = ? AND is_correct = 1 AND attempt_number = 2 AND needed_retry = 1""",
            (lid,)
        ).fetchone()["c"]

        missed = conn.execute(
            """SELECT COUNT(DISTINCT question_hash) as c FROM attempts a1
               WHERE a1.lesson_id = ? AND a1.is_correct = 0 AND a1.attempt_number = 2
               AND NOT EXISTS (
                   SELECT 1 FROM attempts a2
                   WHERE a2.question_hash = a1.question_hash
                   AND a2.is_correct = 1 AND a2.attempt_number = 1
               )""",
            (lid,)
        ).fetchone()["c"]

        total_sessions = conn.execute(
            "SELECT COUNT(*) as c FROM sessions WHERE lesson_id = ? AND finished_at IS NOT NULL",
            (lid,)
        ).fetchone()["c"]

        p = first_try / unique_q if unique_q > 0 else 0

        print(f"  {lid} — {name}")
        print(f"    Sessions: {total_sessions}  |  Questions: {unique_q}")
        print(f"    First-try: {first_try}/{unique_q} ({_pct(first_try, unique_q)})  |  After retry: {retry_ok}  |  Missed: {missed}")
        print(f"    95% CI: {_ci95(p, unique_q)}")
        print()


def problem_questions(conn):
    print()
    print("=" * 70)
    print("  WEAK SPOTS — Questions You Consistently Miss")
    print("=" * 70)
    print()

    questions = conn.execute(
        """SELECT lesson_id, question_hash, question_text,
                  COUNT(*) as total_attempts,
                  SUM(CASE WHEN is_correct = 1 AND attempt_number = 1 THEN 1 ELSE 0 END) as first_try_correct,
                  SUM(CASE WHEN is_correct = 0 AND attempt_number = 2 THEN 1 ELSE 0 END) as twice_wrong
           FROM attempts
           GROUP BY lesson_id, question_hash
           HAVING twice_wrong >= 1
           ORDER BY twice_wrong DESC, total_attempts DESC
           LIMIT 25"""
    ).fetchall()

    if not questions:
        print("  No questions missed twice yet. Great work!\n")
        return

    for q in questions:
        lid = q["lesson_id"]
        name = _lesson_display(lid)
        text = q["question_text"]
        if len(text) > 65:
            text = text[:62] + "..."
        print(f"  [{lid}] {name}")
        print(f"    Q: {text}")
        print(f"    Missed twice: {q['twice_wrong']}x  |  First-try correct: {q['first_try_correct']}x  |  Total attempts: {q['total_attempts']}")
        print()


def learning_trends(conn):
    print()
    print("=" * 70)
    print("  LEARNING TRENDS — Accuracy Over Time")
    print("=" * 70)
    print()

    sessions = conn.execute(
        """SELECT s.id, s.lesson_id, s.started_at, s.finished_at,
                  s.total_questions, s.first_try_correct,
                  s.after_retry_correct, s.final_incorrect
           FROM sessions s
           WHERE s.finished_at IS NOT NULL
           ORDER BY s.started_at ASC"""
    ).fetchall()

    if len(sessions) < 2:
        print("  Need at least 2 completed sessions to show trends.\n")
        return

    print(f"  {'Date':<12} {'Lesson':<10} {'1st-Try':>8} {'After-R':>8} {'Missed':>8} {'Total':>8} {'1st%':>7}")
    print(f"  {'─' * 70}")

    first_try_rates = []

    for s in sessions:
        date = s["started_at"][:10]
        lid = s["lesson_id"]
        total = s["total_questions"] or 0
        ft = s["first_try_correct"] or 0
        ar = s["after_retry_correct"] or 0
        fi = s["final_incorrect"] or 0
        pct = f"{ft / total * 100:.0f}%" if total > 0 else "N/A"
        first_try_rates.append(ft / total if total > 0 else 0)
        print(f"  {date:<12} {lid:<10} {ft:>8} {ar:>8} {fi:>8} {total:>8} {pct:>7}")

    if len(first_try_rates) >= 3:
        n = len(first_try_rates)
        half = n // 2
        early_avg = sum(first_try_rates[:half]) / half
        recent_avg = sum(first_try_rates[half:]) / (n - half)
        improvement = recent_avg - early_avg

        print()
        if improvement > 0:
            print(f"  Trend: IMPROVING  (+{improvement * 100:.1f}pp first-try rate from early to recent sessions)")
        elif improvement < -0.02:
            print(f"  Trend: DECLINING  ({improvement * 100:.1f}pp first-try rate from early to recent sessions)")
        else:
            print(f"  Trend: STABLE  (first-try rate ~{recent_avg * 100:.1f}%)")
    print()


def retention(conn):
    print()
    print("=" * 70)
    print("  RETENTION — Questions Revisited")
    print("=" * 70)
    print()

    repeated = conn.execute(
        """SELECT lesson_id, question_hash, question_text,
                  COUNT(DISTINCT 
                    CASE WHEN is_correct = 1 AND attempt_number = 1 THEN 1 END
                  ) as sessions_first_try,
                  COUNT(*) as total_attempts,
                  SUM(CASE WHEN is_correct = 1 AND attempt_number = 1 THEN 1 ELSE 0 END) as first_try_count,
                  SUM(CASE WHEN is_correct = 0 AND attempt_number = 2 THEN 1 ELSE 0 END) as twice_wrong_count
           FROM attempts
           GROUP BY lesson_id, question_hash
           HAVING COUNT(DISTINCT 
             CAST(substr(timestamp, 1, 10) AS TEXT)
           ) > 1
           ORDER BY total_attempts DESC
           LIMIT 20"""
    ).fetchall()

    if not repeated:
        print("  No questions revisited across multiple days yet.\n")
        return

    print(f"  {'Lesson':<10} {'Question (truncated)':<40} {'Attempts':>8} {'1st-Try':>8} {'Missed2x':>8}")
    print(f"  {'─' * 78}")

    for q in repeated:
        lid = q["lesson_id"]
        text = q["question_text"]
        if len(text) > 38:
            text = text[:35] + "..."
        print(f"  {lid:<10} {text:<40} {q['total_attempts']:>8} {q['first_try_count']:>8} {q['twice_wrong_count']:>8}")
    print()


def mastery_levels(conn):
    print()
    print("=" * 70)
    print("  MASTERY LEVELS BY LESSON")
    print("=" * 70)
    print()

    lessons = conn.execute(
        "SELECT DISTINCT lesson_id FROM attempts ORDER BY lesson_id"
    ).fetchall()

    for row in lessons:
        lid = row["lesson_id"]
        name = _lesson_display(lid)

        questions = conn.execute(
            """SELECT question_hash, question_text,
                      SUM(CASE WHEN is_correct = 1 AND attempt_number = 1 THEN 1 ELSE 0 END) as first_try,
                      SUM(CASE WHEN is_correct = 0 AND attempt_number = 2 THEN 1 ELSE 0 END) as twice_wrong,
                      COUNT(*) as total
               FROM attempts
               WHERE lesson_id = ?
               GROUP BY question_hash""",
            (lid,)
        ).fetchall()

        mastered = sum(1 for q in questions if q["first_try"] > 0 and q["twice_wrong"] == 0 and q["first_try"] >= 1)
        learning = sum(1 for q in questions if q["twice_wrong"] > 0 and q["first_try"] > 0)
        struggling = sum(1 for q in questions if q["twice_wrong"] > 0 and q["first_try"] == 0)
        unseen = 0

        total_q = len(questions)

        if total_q == 0:
            continue

        print(f"  {lid} — {name}")
        print(f"    Mastered (1st-try correct, never missed twice):  {mastered:>3}/{total_q}")
        print(f"    Learning  (missed once, but got 1st-try later):  {learning:>3}/{total_q}")
        print(f"    Struggling (missed twice, never 1st-try correct): {struggling:>3}/{total_q}")

        p = mastered / total_q if total_q > 0 else 0

        if p >= 0.85:
            level = "ADVANCED"
            bar = "\u2588" * 10
        elif p >= 0.65:
            level = "PROFICIENT"
            bar = "\u2588" * 7 + "\u2591" * 3
        elif p >= 0.45:
            level = "DEVELOPING"
            bar = "\u2588" * 5 + "\u2591" * 5
        else:
            level = "BEGINNER"
            bar = "\u2588" * 2 + "\u2591" * 8

        print(f"    Mastery:  [{bar}] {p * 100:.0f}% — {level}")
        print()


def spaced_repetition_suggestions(conn):
    print()
    print("=" * 70)
    print("  SUGGESTED REVIEW — Questions to Revisit")
    print("=" * 70)
    print()

    weak = conn.execute(
        """SELECT lesson_id, question_hash, question_text,
                  SUM(CASE WHEN is_correct = 0 AND attempt_number = 2 THEN 1 ELSE 0 END) as twice_wrong,
                  SUM(CASE WHEN is_correct = 1 AND attempt_number = 1 THEN 1 ELSE 0 END) as first_try,
                  COUNT(*) as total,
                  MAX(timestamp) as last_seen
           FROM attempts
           GROUP BY lesson_id, question_hash
           HAVING twice_wrong >= 1
           ORDER BY twice_wrong DESC, first_try ASC, last_seen ASC
           LIMIT 15"""
    ).fetchall()

    if not weak:
        print("  No weak spots found yet. Keep practicing!\n")
        return

    for q in weak:
        lid = q["lesson_id"]
        name = _lesson_display(lid)
        text = q["question_text"]
        if len(text) > 60:
            text = text[:57] + "..."
        last = q["last_seen"][:10] if q["last_seen"] else "N/A"
        print(f"  [{lid}] {name}")
        print(f"    \"{text}\"")
        print(f"    Missed twice: {q['twice_wrong']}x  |  1st-try correct: {q['first_try']}x  |  Last seen: {last}")
        print()


def statistical_summary(conn):
    print()
    print("=" * 70)
    print("  STATISTICAL SUMMARY")
    print("=" * 70)
    print()

    total = conn.execute("SELECT COUNT(DISTINCT question_hash) as c FROM attempts").fetchone()["c"]
    first_try = conn.execute(
        "SELECT COUNT(DISTINCT question_hash) as c FROM attempts WHERE is_correct = 1 AND attempt_number = 1"
    ).fetchone()["c"]

    if total == 0:
        print("  No data yet.\n")
        return

    p = first_try / total
    se = math.sqrt(p * (1 - p) / total) if 0 < p < 1 else 0
    z = 1.96
    lo = max(0, p - z * se)
    hi = min(1, p + z * se)

    print(f"  First-try accuracy rate:  {first_try}/{total} = {p * 100:.1f}%")
    print(f"  95% confidence interval: [{lo * 100:.1f}%, {hi * 100:.1f}%]")
    print(f"  Standard error:          {se * 100:.2f}%")
    print()

    attempts_per_q = conn.execute(
        "SELECT question_hash, COUNT(*) as c FROM attempts GROUP BY question_hash"
    ).fetchall()
    counts = [row["c"] for row in attempts_per_q]
    n = len(counts)
    mean_attempts = sum(counts) / n if n > 0 else 0
    variance = sum((c - mean_attempts) ** 2 for c in counts) / n if n > 0 else 0
    std_dev = math.sqrt(variance)

    print(f"  Avg attempts per question:  {mean_attempts:.2f}")
    print(f"  Std dev of attempts:        {std_dev:.2f}")
    print(f"  Min attempts:               {min(counts) if counts else 0}")
    print(f"  Max attempts:               {max(counts) if counts else 0}")
    print()

    session_counts = conn.execute(
        "SELECT lesson_id, COUNT(*) as c FROM sessions WHERE finished_at IS NOT NULL GROUP BY lesson_id ORDER BY lesson_id"
    ).fetchall()
    print("  Sessions per lesson:")
    for row in session_counts:
        lid = row["lesson_id"]
        name = _lesson_display(lid)
        print(f"    {lid} ({name}): {row['c']} sessions")

    print()

    lesson_accuracies = conn.execute(
        """SELECT lesson_id,
                  COUNT(DISTINCT question_hash) as total_q,
                  SUM(CASE WHEN is_correct = 1 AND attempt_number = 1 THEN 1 ELSE 0 END) as first_try
           FROM attempts
           GROUP BY lesson_id
           ORDER BY lesson_id"""
    ).fetchall()

    print("  First-try accuracy by lesson:")
    best = None
    worst = None
    for row in lesson_accuracies:
        lid = row["lesson_id"]
        name = _lesson_display(lid)
        t = row["total_q"]
        ft = row["first_try"]
        rate = ft / t if t > 0 else 0
        label = f"{rate * 100:.1f}%"
        print(f"    {lid} ({name}): {ft}/{t} = {label}")
        if best is None or rate > best[1]:
            best = (name, rate)
        if worst is None or rate < worst[1]:
            worst = (name, rate)

    if best and worst:
        print()
        print(f"  Strongest lesson: {best[0]} ({best[1] * 100:.1f}%)")
        print(f"  Weakest lesson:   {worst[0]} ({worst[1] * 100:.1f}%)")

    print()


def main():
    conn = _get_db()
    if conn is None:
        print(f"\n  No progress database found at {DB_PATH}")
        print("  Run a lesson first to create some data.\n")
        sys.exit(1)

    has_data = overview(conn)
    if not has_data:
        conn.close()
        return

    per_lesson(conn)
    problem_questions(conn)
    learning_trends(conn)
    retention(conn)
    mastery_levels(conn)
    spaced_repetition_suggestions(conn)
    statistical_summary(conn)

    conn.close()


if __name__ == "__main__":
    main()