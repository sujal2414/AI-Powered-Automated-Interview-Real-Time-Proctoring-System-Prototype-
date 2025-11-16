# question_generator.py
import os
import re
try:
    import openai
except Exception:
    openai = None

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def _parse_questions_from_text(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    qs = []
    for l in lines:
        q = re.sub(r'^\d+\s*[\.\)]\s*', '', l)
        qs.append(q)
    return qs

def generate_questions_for_subject(subject: str, n: int = 5):
    """
    Use OpenAI to generate n subject-specific questions.
    Raises RuntimeError if OpenAI is not configured.
    """
    if OPENAI_API_KEY is None or openai is None:
        raise RuntimeError("OpenAI not configured or 'openai' library missing.")
    openai.api_key = OPENAI_API_KEY
    prompt = f"Generate {n} interview questions for the subject: {subject}. Provide a numbered list, concise questions, gradually increasing difficulty."
    resp = openai.ChatCompletion.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "You are an expert technical interviewer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
        temperature=0.25,
        n=1
    )
    # extract content safely
    content = ""
    if isinstance(resp, dict):
        content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
    else:
        try:
            content = resp.choices[0].message.content
        except Exception:
            content = str(resp)
    qs = _parse_questions_from_text(content)
    if len(qs) < n:
        import re
        sents = re.split(r'(?<=[\.\?\!])\s+', content)
        for s in sents:
            s = s.strip()
            if s and len(qs) < n:
                qs.append(s)
    return qs[:n]

def generate_counter_question(previous_question: str, candidate_answer: str, history=None, max_tokens=60):
    """
    Generate a single concise follow-up question based on candidate_answer.
    Returns string follow-up question. Uses OpenAI if configured, otherwise a heuristic fallback.
    """
    if history is None:
        history = []

    # Build prompt
    prompt_system = (
        "You are an expert interviewer. Generate exactly one concise, relevant follow-up question "
        "that asks for clarification, a deeper explanation, or a concrete example based only on the candidate's answer. "
        "Keep it short (<= 25 words) and professional."
    )
    user_content = f"Previous question: {previous_question}\n\nCandidate answer: {candidate_answer}"
    if history:
        user_content += "\n\nRecent history:\n" + "\n".join(history[-3:])

    # Try OpenAI
    if OPENAI_API_KEY and openai is not None:
        try:
            openai.api_key = OPENAI_API_KEY
            resp = openai.ChatCompletion.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=max_tokens,
                temperature=0.2,
                n=1
            )
            # parse resp
            content = ""
            if isinstance(resp, dict):
                content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                content = getattr(resp.choices[0].message, "content", str(resp))
            if content:
                return content.strip().replace("\n", " ")
        except Exception:
            # fall through to heuristic fallback
            pass

    # Heuristic fallback
    a = (candidate_answer or "").lower()
    if any(word in a for word in ["because", "since", "so that", "therefore"]):
        return "Can you give a concrete example to illustrate that?"
    if any(word in a for word in ["for example", "e.g.", "such as"]):
        return "Can you explain the steps you took in that example?"
    if any(term in a for term in ["algorithm", "data", "model", "architecture", "thread", "process", "api", "hash"]):
        return "Can you explain the technical steps or rationale in more detail?"
    if len(a.split()) < 10:
        return "Could you expand on that with more detail or an example?"
    return "Can you provide more detail or a specific example to illustrate your point?"
