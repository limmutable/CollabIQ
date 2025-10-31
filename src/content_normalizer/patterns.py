"""
Signature detection patterns for ContentNormalizer.

This module defines regex patterns and heuristics for detecting email signatures
in both Korean and English text. Patterns are based on contract specifications
in contracts/content_normalizer.yaml.

Tasks:
- T052: Pattern library module
- T053: Korean signature patterns
- T054: English signature patterns
- T055: Heuristic fallback patterns
"""

import re
from typing import Optional, List, Tuple


# ============================================================================
# Korean Signature Patterns (T053)
# ============================================================================

# Pattern 1: korean_thanks_name
# Matches: "감사합니다.\n이름 드림" or variations
KOREAN_THANKS_NAME = re.compile(
    r'(감사합니다|감사드립니다|고맙습니다)\s*[.。]?\s*\n+\s*([가-힣]{2,4})\s+(드림|올림)',
    re.MULTILINE | re.UNICODE
)

# Pattern 2: korean_greeting_signature
# Matches: "좋은 하루 보내세요.\n이름 드림" or variations
KOREAN_GREETING_SIGNATURE = re.compile(
    r'(좋은\s+하루\s+보내세요|행복한\s+하루\s+되세요|건강하세요)\s*[.。]?\s*\n+\s*([가-힣]{2,4})\s+(드림|올림)',
    re.MULTILINE | re.UNICODE
)

# Pattern 3: korean_closing_only
# Matches: "감사합니다." or "고맙습니다." at end of email (no name)
KOREAN_CLOSING_ONLY = re.compile(
    r'\n+(감사합니다|감사드립니다|고맙습니다|수고하세요)\s*[.。]?\s*$',
    re.MULTILINE | re.UNICODE
)

# Pattern 4: korean_name_only
# Matches: "이름 드림" at end of email
KOREAN_NAME_ONLY = re.compile(
    r'\n+\s*([가-힣]{2,4})\s+(드림|올림)\s*$',
    re.MULTILINE | re.UNICODE
)

# Pattern 5: korean_contact_block
# Matches: Contact information block in Korean (name, title, company, contact)
KOREAN_CONTACT_BLOCK = re.compile(
    r'\n+[-=]{3,}\s*\n+\s*([가-힣]{2,4})\s+(부장|과장|대리|팀장|이사|대표|매니저)',
    re.MULTILINE | re.UNICODE
)


# ============================================================================
# English Signature Patterns (T054)
# ============================================================================

# Pattern 1: english_formal_closing
# Matches: "Best regards,\nJohn Smith" or similar formal closings
ENGLISH_FORMAL_CLOSING = re.compile(
    r'\n+(Best\s+regards|Kind\s+regards|Sincerely|Regards|Yours\s+sincerely|Yours\s+truly)\s*,?\s*\n+\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
    re.MULTILINE | re.IGNORECASE
)

# Pattern 2: english_informal_closing
# Matches: "Thanks,\nEmma" or "Cheers,\nMike"
ENGLISH_INFORMAL_CLOSING = re.compile(
    r'\n+(Thanks|Thank\s+you|Cheers|Best)\s*,?\s*\n+\s*([A-Z][a-z]+)',
    re.MULTILINE | re.IGNORECASE
)

# Pattern 3: english_contact_block
# Matches: Contact information block (name, title, company, phone, email)
ENGLISH_CONTACT_BLOCK = re.compile(
    r'\n+[-=]{3,}\s*\n+\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\s*\n+\s*(.*?(Manager|Director|CEO|President|VP|Engineer))',
    re.MULTILINE | re.IGNORECASE
)

# Pattern 4: english_phone_email_block
# Matches: Block with phone number and/or email
ENGLISH_PHONE_EMAIL_BLOCK = re.compile(
    r'\n+(Phone:|Mobile:|Tel:|Email:).+',
    re.MULTILINE | re.IGNORECASE
)

# Pattern 5: english_confidentiality_notice
# Matches: Confidentiality or legal disclaimer at end
ENGLISH_CONFIDENTIALITY_NOTICE = re.compile(
    r'\n+(CONFIDENTIALITY\s+NOTICE|DISCLAIMER|LEGAL\s+NOTICE):.+',
    re.MULTILINE | re.IGNORECASE
)


# ============================================================================
# Heuristic Fallback Patterns (T055)
# ============================================================================

# Heuristic 1: separator_line_signature
# Matches: Separator line (---, ===, ___) followed by text
SEPARATOR_LINE_SIGNATURE = re.compile(
    r'\n+\s*[-=_]{3,}\s*\n+',
    re.MULTILINE
)

# Heuristic 2: short_final_line
# Detects if last 1-2 lines are very short (< 50 chars) and likely signature
def detect_short_final_line(text: str, max_lines: int = 2, max_chars: int = 50) -> Optional[int]:
    """
    Heuristic: Detect if last few lines are very short (likely signature).

    Args:
        text: Email body text
        max_lines: Number of final lines to check (default: 2)
        max_chars: Maximum characters to consider "short" (default: 50)

    Returns:
        Starting position of likely signature, or None if not detected
    """
    if not text:
        return None

    lines = text.split('\n')
    if len(lines) < max_lines:
        return None

    # Check last N lines
    final_lines = lines[-max_lines:]
    final_text = '\n'.join(final_lines)

    # If all final lines are short and non-empty, likely signature
    if 0 < len(final_text.strip()) <= max_chars:
        # Find start position of these lines
        start_pos = len(text) - len(final_text)
        return start_pos

    return None


# Heuristic 3: repeated_pattern_detection
# Detects if similar pattern appears across multiple emails (learning-based)
# TODO: Implement in future with pattern frequency tracking


# ============================================================================
# Pattern Matching Functions
# ============================================================================

def find_korean_signature(text: str) -> Optional[Tuple[int, str]]:
    """
    Search for Korean signature patterns in text.

    Args:
        text: Email body text

    Returns:
        Tuple of (start_position, pattern_name) if found, else None
    """
    patterns = [
        (KOREAN_THANKS_NAME, "korean_thanks_name"),
        (KOREAN_GREETING_SIGNATURE, "korean_greeting_signature"),
        (KOREAN_CONTACT_BLOCK, "korean_contact_block"),
        (KOREAN_NAME_ONLY, "korean_name_only"),
        (KOREAN_CLOSING_ONLY, "korean_closing_only"),
    ]

    for pattern, name in patterns:
        match = pattern.search(text)
        if match:
            return (match.start(), name)

    return None


def find_english_signature(text: str) -> Optional[Tuple[int, str]]:
    """
    Search for English signature patterns in text.

    Args:
        text: Email body text

    Returns:
        Tuple of (start_position, pattern_name) if found, else None
    """
    patterns = [
        (ENGLISH_FORMAL_CLOSING, "english_formal_closing"),
        (ENGLISH_INFORMAL_CLOSING, "english_informal_closing"),
        (ENGLISH_CONTACT_BLOCK, "english_contact_block"),
        (ENGLISH_PHONE_EMAIL_BLOCK, "english_phone_email_block"),
        (ENGLISH_CONFIDENTIALITY_NOTICE, "english_confidentiality_notice"),
    ]

    for pattern, name in patterns:
        match = pattern.search(text)
        if match:
            return (match.start(), name)

    return None


def find_heuristic_signature(text: str) -> Optional[Tuple[int, str]]:
    """
    Search for signature using heuristic patterns (fallback).

    Args:
        text: Email body text

    Returns:
        Tuple of (start_position, pattern_name) if found, else None
    """
    # Try separator line
    match = SEPARATOR_LINE_SIGNATURE.search(text)
    if match:
        return (match.start(), "separator_line_signature")

    # Try short final line heuristic
    start_pos = detect_short_final_line(text)
    if start_pos is not None:
        return (start_pos, "short_final_line")

    return None


def detect_signature(text: str) -> Optional[Tuple[int, str]]:
    """
    Detect signature in email text using all available patterns.

    Tries patterns in order:
    1. Korean patterns
    2. English patterns
    3. Heuristic patterns (fallback)

    Args:
        text: Email body text

    Returns:
        Tuple of (start_position, pattern_name) if signature found, else None

    Examples:
        >>> result = detect_signature("안녕하세요.\n\n감사합니다.\n김철수 드림")
        >>> result[0]  # Start position of signature
        14
        >>> result[1]  # Pattern name
        'korean_thanks_name'
    """
    if not text or not text.strip():
        return None

    # Try Korean patterns first
    result = find_korean_signature(text)
    if result:
        return result

    # Try English patterns
    result = find_english_signature(text)
    if result:
        return result

    # Fall back to heuristics
    result = find_heuristic_signature(text)
    if result:
        return result

    return None


def remove_signature(text: str) -> str:
    """
    Remove detected signature from email text.

    Args:
        text: Email body text

    Returns:
        Text with signature removed, or original text if no signature detected

    Examples:
        >>> text = "Hello,\\n\\nContent here.\\n\\nBest regards,\\nJohn"
        >>> remove_signature(text)
        'Hello,\\n\\nContent here.'
    """
    result = detect_signature(text)
    if result is None:
        return text

    signature_start, pattern_name = result

    # Remove signature from text
    cleaned_text = text[:signature_start].rstrip()

    return cleaned_text


# ============================================================================
# Quoted Thread Patterns (T067-T069)
# ============================================================================

# Pattern 1: angle_bracket_quotes
# Matches: Lines starting with "> " (standard email quote prefix)
ANGLE_BRACKET_QUOTES = re.compile(
    r'^>.*$',
    re.MULTILINE
)

# Pattern 2: gmail_reply_header (English)
# Matches: "On Mon, Oct 30, 2025 at 2:30 PM, John Smith wrote:"
GMAIL_REPLY_HEADER = re.compile(
    r'On\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}'
    r'(?:\s+at\s+\d{1,2}:\d{2}\s*(?:AM|PM)?)?'
    r',?\s+.+?\s+wrote:',
    re.MULTILINE | re.IGNORECASE
)

# Pattern 3: outlook_reply_header (English)
# Matches: "From: John Smith\nSent: Monday, October 30, 2025"
OUTLOOK_REPLY_HEADER = re.compile(
    r'^From:\s*.+\n'
    r'Sent:\s*(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*'
    r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
    re.MULTILINE | re.IGNORECASE
)

# Pattern 4: korean_reply_header
# Matches: "2025년 10월 30일 화요일, 김철수님이 작성:"
KOREAN_REPLY_HEADER = re.compile(
    r'\d{4}년\s+\d{1,2}월\s+\d{1,2}일\s+(?:월|화|수|목|금|토|일)요일,?\s*.+?(?:님이\s*작성|wrote):',
    re.MULTILINE | re.UNICODE
)

# Pattern 5: simple_on_date_wrote
# Matches: "On [date]... wrote:" (more flexible than Gmail-specific)
SIMPLE_ON_DATE_WROTE = re.compile(
    r'On\s+.+?\s+wrote:',
    re.MULTILINE | re.IGNORECASE
)


# ============================================================================
# Quoted Thread Detection Functions
# ============================================================================

def find_quoted_thread(text: str) -> Optional[Tuple[int, str]]:
    """
    Search for quoted thread patterns in text.

    Args:
        text: Email body text

    Returns:
        Tuple of (start_position, pattern_name) if found, else None
    """
    if not text or not text.strip():
        return None

    # Try reply headers first (more specific)
    patterns = [
        (GMAIL_REPLY_HEADER, "gmail_reply_header"),
        (OUTLOOK_REPLY_HEADER, "outlook_reply_header"),
        (KOREAN_REPLY_HEADER, "korean_reply_header"),
        (SIMPLE_ON_DATE_WROTE, "simple_on_date_wrote"),
    ]

    for pattern, name in patterns:
        match = pattern.search(text)
        if match:
            return (match.start(), name)

    # Try angle bracket quotes (less specific, check last)
    # Find first line starting with ">"
    match = ANGLE_BRACKET_QUOTES.search(text)
    if match:
        return (match.start(), "angle_bracket_quotes")

    return None


def detect_nested_quotes(text: str) -> Optional[int]:
    """
    Detect nested quoted content (multiple levels of ">").

    This handles cases like:
    > Level 1 quote
    > > Level 2 quote
    > > > Level 3 quote

    Args:
        text: Email body text

    Returns:
        Starting position of first quote line, or None
    """
    # Find first line with "> " (any level)
    match = re.search(r'^>\s*.*$', text, re.MULTILINE)
    if match:
        return match.start()
    return None


def detect_quoted_thread(text: str) -> Optional[Tuple[int, str]]:
    """
    Detect quoted thread in email text using all available patterns.

    Tries patterns in order:
    1. Reply headers ("On [date] wrote:", Korean headers)
    2. Angle bracket quotes ("> ")
    3. Nested quotes

    Args:
        text: Email body text

    Returns:
        Tuple of (start_position, pattern_name) if quoted thread found, else None

    Examples:
        >>> text = "Thanks!\\n\\n> On Oct 30, John wrote:\\n> Previous message"
        >>> result = detect_quoted_thread(text)
        >>> result[0]  # Start position
        9
        >>> result[1]  # Pattern name
        'angle_bracket_quotes'
    """
    result = find_quoted_thread(text)
    if result:
        return result

    # Try nested quote detection as fallback
    pos = detect_nested_quotes(text)
    if pos is not None:
        return (pos, "nested_quotes")

    return None


def remove_quoted_thread(text: str) -> str:
    """
    Remove detected quoted thread from email text.

    Args:
        text: Email body text

    Returns:
        Text with quoted thread removed, or original text if no quotes detected

    Examples:
        >>> text = "New message\\n\\n> Quoted text"
        >>> remove_quoted_thread(text)
        'New message'
    """
    if not text or not text.strip():
        return text

    result = detect_quoted_thread(text)
    if result is None:
        return text

    quote_start, pattern_name = result

    # Remove quoted thread from text
    cleaned_text = text[:quote_start].rstrip()

    return cleaned_text


# ============================================================================
# Pattern Statistics and Debugging
# ============================================================================

def get_all_patterns() -> List[Tuple[str, re.Pattern]]:
    """
    Get list of all compiled regex patterns for debugging.

    Returns:
        List of (pattern_name, compiled_pattern) tuples
    """
    return [
        ("korean_thanks_name", KOREAN_THANKS_NAME),
        ("korean_greeting_signature", KOREAN_GREETING_SIGNATURE),
        ("korean_closing_only", KOREAN_CLOSING_ONLY),
        ("korean_name_only", KOREAN_NAME_ONLY),
        ("korean_contact_block", KOREAN_CONTACT_BLOCK),
        ("english_formal_closing", ENGLISH_FORMAL_CLOSING),
        ("english_informal_closing", ENGLISH_INFORMAL_CLOSING),
        ("english_contact_block", ENGLISH_CONTACT_BLOCK),
        ("english_phone_email_block", ENGLISH_PHONE_EMAIL_BLOCK),
        ("english_confidentiality_notice", ENGLISH_CONFIDENTIALITY_NOTICE),
        ("separator_line_signature", SEPARATOR_LINE_SIGNATURE),
    ]


def test_pattern_on_text(pattern_name: str, text: str) -> bool:
    """
    Test specific pattern against text (for debugging).

    Args:
        pattern_name: Name of pattern to test
        text: Text to test against

    Returns:
        True if pattern matches, False otherwise
    """
    patterns = dict(get_all_patterns())
    if pattern_name not in patterns:
        raise ValueError(f"Unknown pattern: {pattern_name}")

    pattern = patterns[pattern_name]
    return pattern.search(text) is not None
