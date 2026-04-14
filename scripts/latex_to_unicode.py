#!/usr/bin/env python3
"""
LaTeX 数学公式 -> Unicode 转换器
针对微信/QQ 可读性优化
"""

import re
import sys


Latex_TO_UNICODE = [
    (r'\alpha', 'α'), (r'\beta', 'β'), (r'\gamma', 'γ'), (r'\delta', 'δ'),
    (r'\epsilon', 'ε'), (r'\zeta', 'ζ'), (r'\eta', 'η'), (r'\theta', 'θ'),
    (r'\iota', 'ι'), (r'\kappa', 'κ'), (r'\lambda', 'λ'), (r'\mu', 'μ'),
    (r'\nu', 'ν'), (r'\xi', 'ξ'), (r'\pi', 'π'), (r'\rho', 'ρ'),
    (r'\sigma', 'σ'), (r'\tau', 'τ'), (r'\upsilon', 'υ'), (r'\phi', 'φ'),
    (r'\chi', 'χ'), (r'\psi', 'ψ'), (r'\omega', 'ω'),
    (r'\Alpha', 'Α'), (r'\Beta', 'Β'), (r'\Gamma', 'Γ'), (r'\Delta', 'Δ'),
    (r'\Theta', 'Θ'), (r'\Lambda', 'Λ'), (r'\Xi', 'Ξ'), (r'\Pi', 'Π'),
    (r'\Sigma', 'Σ'), (r'\Phi', 'Φ'), (r'\Psi', 'Ψ'), (r'\Omega', 'Ω'),
    (r'\times', '×'), (r'\div', '÷'), (r'\pm', '±'), (r'\mp', '∓'),
    (r'\cdot', '·'), (r'\leq', '≤'), (r'\geq', '≥'), (r'\neq', '≠'),
    (r'\approx', '≈'), (r'\equiv', '≡'), (r'\infty', '∞'),
    (r'\partial', '∂'), (r'\nabla', '∇'), (r'\forall', '∀'), (r'\exists', '∃'),
    (r'\in', '∈'), (r'\notin', '∉'), (r'\subset', '⊂'), (r'\supset', '⊃'),
    (r'\cup', '∪'), (r'\cap', '∩'), (r'\emptyset', '∅'),
    (r'\land', '∧'), (r'\lor', '∨'), (r'\neg', '¬'), (r'\to', '→'),
    (r'\rightarrow', '→'), (r'\leftarrow', '←'),
    (r'\Rightarrow', '⇒'), (r'\Leftarrow', '⇐'), (r'\leftrightarrow', '↔'),
    (r'\sum', '∑'), (r'\prod', '∏'), (r'\int', '∫'), (r'\oint', '∮'),
    (r'\sqrt', '√'), (r'\angle', '∠'), (r'\perp', '⊥'), (r'\parallel', '∥'),
    (r'\triangle', '△'), (r'\circ', '○'), (r'\bullet', '•'),
    (r'\mathbb{R}', 'ℝ'), (r'\mathbb{N}', 'ℕ'), (r'\mathbb{Z}', 'ℤ'),
    (r'\mathbb{Q}', 'ℚ'), (r'\mathbb{C}', 'ℂ'),
    (r'\degree', '°'), (r'\therefore', '∴'), (r'\because', '∵'),
    (r'\cdots', '⋯'), (r'\ldots', '…'), (r'\vdots', '⋮'), (r'\ddots', '⋱'),
    (r'\prime', '′'), (r'\hbar', 'ℏ'), (r'\checkmark', '✓'),
    (r'\blacksquare', '■'), (r'\square', '□'),
    (r'^2', '²'), (r'^3', '³'), (r'^4', '⁴'), (r'^5', '⁵'),
    (r'^6', '⁶'), (r'^7', '⁷'), (r'^8', '⁸'), (r'^9', '⁹'), (r'^0', '⁰'),
    ('_0', '₀'), ('_1', '₁'), ('_2', '₂'), ('_3', '₃'), ('_4', '₄'),
    ('_5', '₅'), ('_6', '₆'), ('_7', '₇'), ('_8', '₈'), ('_9', '₉'),
]

SUB_LATIN = {
    'a':'ₐ','e':'ₑ','h':'ₕ','i':'ᵢ','j':'ⱼ','k':'ₖ','l':'ₗ','m':'ₘ',
    'n':'ₙ','o':'ₒ','p':'ₚ','r':'ᵣ','s':'ₛ','t':'ₜ','u':'ᵤ','v':'ᵥ','x':'ₓ'
}
SUP_LATIN = {
    'a':'ᵃ','b':'ᵇ','c':'ᶜ','d':'ᵈ','e':'ᵉ','f':'ᶠ','g':'ᵍ','h':'ʰ','i':'ᶦ',
    'j':'ʲ','k':'ᵏ','l':'ˡ','m':'ᵐ','n':'ⁿ','o':'ᵒ','p':'ᵖ','r':'ʳ','s':'ˢ',
    't':'ᵗ','u':'ᵘ','v':'ᵛ','w':'ʷ','x':'ˣ','y':'ʸ','z':'ᶻ'
}


def _match_brace(s, start):
    """Find matching close brace for the '{' at position start (depth-counting)."""
    if start >= len(s) or s[start] != '{':
        return None, start
    depth = 0
    i = start
    while i < len(s):
        if s[i] == '{': depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                return s[start+1:i], i + 1
        i += 1
    return None, start


def _sub_chars(s):
    """Convert a string to Unicode subscript characters."""
    out = []
    for c in s:
        if c in SUB_LATIN:
            out.append(SUB_LATIN[c])
        elif c.isdigit():
            subs = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄',
                    '5':'₅','6':'₆','7':'₇','8':'₈','9':'₉'}
            out.append(subs.get(c, c))
        else:
            out.append(c)
    return ''.join(out)


def _sup_chars(s):
    """Convert a string to Unicode superscript characters."""
    out = []
    for c in s:
        if c in SUP_LATIN:
            out.append(SUP_LATIN[c])
        elif c.isdigit():
            sups = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴',
                    '5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}
            out.append(sups.get(c, c))
        else:
            out.append(c)
    return ''.join(out)


UNICODE_FRACS = {
    ('1','2'):'½', ('1','3'):'⅓', ('2','3'):'⅔',
    ('1','4'):'¼', ('3','4'):'¾', ('1','5'):'⅕',
    ('2','5'):'⅖', ('3','5'):'⅗', ('4','5'):'⅘',
    ('1','6'):'⅙', ('5','6'):'⅚', ('1','8'):'⅛',
    ('3','8'):'⅜', ('5','8'):'⅝', ('7','8'):'⅞',
    ('1','9'):'⅑', ('1','10'):'⅒',
}

def _to_unicode_frac(num, den):
    return UNICODE_FRACS.get((num, den))


def _convert_frac(s):
    """Replace \\frac{num}{den} using brace-counting. Simple -> a/b, else (a)/(b)."""
    result = []
    i = 0
    while i < len(s):
        idx = s.find('\\frac', i)
        if idx == -1:
            result.append(s[i:])
            break
        result.append(s[i:idx])
        i = idx + 5

        num, j = _match_brace(s, i)
        if num is None:
            result.append('\\frac')
            continue
        den, k = _match_brace(s, j)
        if den is None:
            result.append('(' + num + ')')
            i = j
            continue

        # Recursively convert inner content
        num_out = convert_latex(num).strip('『』')
        den_out = convert_latex(den).strip('『』')
        # Strip outer parens if already wrapped
        num_str = num_out[1:-1] if num_out.startswith('(') and num_out.endswith(')') else num_out
        den_str = den_out[1:-1] if den_out.startswith('(') and den_out.endswith(')') else den_out

        # Simple plain numbers/variables -> a/b
        def is_simple(x):
            return bool(x) and not any(c in x for c in '{}\\<>+-')
        if is_simple(num_str) and is_simple(den_str):
            u_frac = _to_unicode_frac(num_str, den_str)
            if u_frac:
                result.append(u_frac)
            else:
                result.append(num_str + '/' + den_str)
        else:
            result.append('(' + num_str + ')/(' + den_str + ')')
        i = k

    return ''.join(result)


def _simplify_frac_coeff(s):
    """Convert fraction coefficient patterns to Unicode fraction characters."""
    def repl_paren(m):
        num, den = m.group(1), m.group(2)
        after = m.group(3)
        u = _to_unicode_frac(num, den)
        if u and after.startswith(' '):
            return u + after
        return '(' + num + ')/(' + den + ')' + after

    s2 = re.sub(r'\((\d+)\)\/\((\d+)\)\) ', repl_paren, s)
    if s2 != s:
        return s2

    def repl_no_paren(m):
        num, den = m.group(1), m.group(2)
        after = m.group(3)
        u = _to_unicode_frac(num, den)
        if u and after.startswith(' '):
            return u + after
        return num + '/' + den + after

    return re.sub(r'^(\d+)/(\d+)\ ', repl_no_paren, s, count=1)


def _strip_text(s):
    """Remove \\text{...}, \\textbf{...} etc."""
    cmds = [r'\text', r'\textbf', r'\textit', r'\mathsf', r'\mathbf',
            r'\mathrm', r'\mathit', r'\texttt', r'\rm', r'\bf', r'\it']
    for cmd in cmds:
        i = 0
        while i < len(s):
            cmd_idx = s.find(cmd, i)
            if cmd_idx == -1:
                break
            content, end = _match_brace(s, cmd_idx + len(cmd))
            if content is not None:
                s = s[:cmd_idx] + content + s[end:]
                i = cmd_idx
            else:
                i = cmd_idx + len(cmd)
    return s


def _expand_subscripts(s):
    """Expand x_{abc} -> Unicode subscript. Handles nested braces via multiple passes."""
    for _ in range(6):
        prev = s
        parts = []
        i = 0
        changed = False
        while i < len(s):
            if s[i] == '_' and i + 1 < len(s) and s[i+1] == '{':
                content, end = _match_brace(s, i+1)
                if content is not None:
                    parts.append(_sub_chars(content))
                    i = end
                    changed = True
                    continue
            elif s[i] == '_' and i + 2 < len(s) and s[i+2:i+3].isalnum():
                c = s[i+1]
                parts.append(_sub_chars(c))
                i += 2
                changed = True
                continue
            elif s[i] == '_' and i + 1 < len(s) and s[i+1].isalnum():
                # Single char subscript at end of string: x_m -> xₘ
                c = s[i+1]
                parts.append(_sub_chars(c))
                i += 2
                changed = True
                continue
            parts.append(s[i])
            i += 1
        s = ''.join(parts)
        if not changed:
            break
    return s


def _expand_superscripts(s):
    """Expand x^{abc} and x^2 -> Unicode superscript."""
    parts = []
    i = 0
    while i < len(s):
        if s[i] == '^' and i + 1 < len(s) and s[i+1] == '{':
            content, end = _match_brace(s, i+1)
            if content is not None:
                parts.append(_sup_chars(content))
                i = end
                continue
        elif s[i] == '^' and i + 2 < len(s) and s[i+1].isalnum():
            parts.append(_sup_chars(s[i+1]))
            i += 2
            continue
        parts.append(s[i])
        i += 1
    return ''.join(parts)


def convert_latex(latex_str):
    """
    Convert a single LaTeX formula (no $$ or $ delimiters).
    """
    result = latex_str

    # Strip \left and \right delimiters before any other processing
    # e.g. \left| -> |, \right| -> |, \left( -> (, \right) -> )
    result = re.sub(r'\\left\s*[|.]', '|', result)
    result = re.sub(r'\\right\s*[|.]', '|', result)
    result = re.sub(r'\\left\s*\(', '(', result)
    result = re.sub(r'\\right\s*\)', ')', result)
    result = re.sub(r'\\left\s*\[', '[', result)
    result = re.sub(r'\\right\s*\]', ']', result)
    result = re.sub(r'\\left\s*\{', '{', result)
    result = re.sub(r'\\right\s*\}', '}', result)

    # Space commands
    result = result.replace('\\quad', ' ')
    result = result.replace('\\qquad', '  ')
    result = result.replace('\\,', ' ')
    result = result.replace('\\;', ' ')
    result = result.replace('\\!', '')
    result = result.replace('\\~', ' ')
    result = result.replace('\\ ', ' ')  # backslash-space
    result = re.sub(r'\\hspace\{[^}]*\}', ' ', result)

    # \\sqrt[n]{x} -> (x)^(1/n) and \\sqrt{x} -> √(x)
    for _ in range(6):
        prev = result
        parts = []
        i = 0
        while i < len(result):
            sqrt_pos = result.find('\\sqrt', i)
            if sqrt_pos == -1:
                parts.append(result[i:])
                break
            parts.append(result[i:sqrt_pos])
            rest = result[sqrt_pos + 5:]  # skip '\sqrt'

            if rest.startswith('['):
                # \sqrt[n]{x}
                bracket_end = rest.find(']')
                if bracket_end != -1 and bracket_end + 1 < len(rest) and rest[bracket_end+1] == '{':
                    n = rest[1:bracket_end]
                    content, end = _match_brace(rest, bracket_end + 1)
                    if content is not None:
                        inner = convert_latex(content).strip('『』')
                        parts.append('(' + inner + ')^(1/' + n + ')')
                        i = 0
                        result = ''.join(parts) + rest[end:]
                        parts = []
                        break
            if rest.startswith('{'):
                content, end = _match_brace(rest, 0)
                if content is not None:
                    inner = convert_latex(content).strip('『』')
                    parts.append('√(' + inner + ')')
                    i = 0
                    result = ''.join(parts) + rest[end:]
                    parts = []
                    break
            parts.append('\\sqrt')
            i = sqrt_pos + 5
        if result == prev:
            break

    # \frac
    result = _convert_frac(result)

    # \binom
    for _ in range(6):
        prev = result
        parts = []
        i = 0
        while i < len(result):
            idx = result.find('\\binom', i)
            if idx == -1:
                parts.append(result[i:])
                break
            parts.append(result[i:idx])
            c1, j = _match_brace(result, idx + 6)
            if c1 is None:
                parts.append('\\binom')
                i = idx + 6
                continue
            c2, k = _match_brace(result, j)
            if c2 is None:
                parts.append('(' + c1 + ')')
                i = j
                continue
            parts.append('C(' + c1 + ',' + c2 + ')')
            i = k
        result = ''.join(parts)
        if result == prev:
            break

    # \boxed{...}
    for _ in range(6):
        prev = result
        parts = []
        i = 0
        while i < len(result):
            idx = result.find('\\boxed', i)
            if idx == -1:
                parts.append(result[i:])
                break
            parts.append(result[i:idx])
            content, end = _match_brace(result, idx + 6)
            if content is not None:
                inner = convert_latex(content).strip('『』')
                parts.append('[答案: ' + inner + ']')
                i = 0
                result = ''.join(parts) + result[end:]
                parts = []
                break
            parts.append('\\boxed')
            i = idx + 6
        if result == prev:
            break

    # \text and other text commands
    result = _strip_text(result)

    # Subscripts and superscripts
    result = _expand_subscripts(result)
    result = _expand_superscripts(result)

    # Greek letters and other LaTeX commands
    for latex, unicode_char in Latex_TO_UNICODE:
        result = result.replace(latex, unicode_char)

    # Clean up remaining braces
    result = re.sub(r'\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\([a-zA-Z]+)', r'\1', result)

    # Smart spacing
    def sp(m): return m.group(1) + ' ' + m.group(2)
    result = re.sub(r'(\d)([a-zA-Z])', sp, result)
    result = re.sub(r'([a-zA-Z])(\d)', sp, result)
    result = re.sub(r'(\d)(\()', sp, result)
    result = re.sub(r'(\))(\d)', sp, result)
    result = re.sub(r'\)\(', ') (', result)
    result = re.sub(r'\s+', ' ', result)

    return result.strip()


def latex_to_unicode(text):
    """Convert LaTeX in full text to Unicode (handles $$...$$ and $...$)."""
    if not text:
        return text
    result = text

    def replace_display(m):
        return '『' + convert_latex(m.group(1)) + '』'
    result = re.sub(r'\$\$(.+?)\$\$', replace_display, result, flags=re.DOTALL)

    def replace_inline(m):
        return convert_latex(m.group(1))
    result = re.sub(r'\$(.+?)\$', replace_inline, result, flags=re.DOTALL)

    return result


# Alias for backwards compatibility
latex_to_plain_text = latex_to_unicode


if __name__ == '__main__':
    tests = [
        r"$\frac{f_{max}}{M}$",
        r"$\frac{2}{4}$",
        r"$\alpha + \beta + \times \div$",
        r"$x^2 + y_1 + \sqrt{2} + \boxed{x}$",
        r"$\frac{1}{2}(a_1 + a_2)$",
        r"$$a_{max} = \frac{f_{max}}{M}$$",
        r"$\frac{\mu mg}{M}$",
        r"$\frac{F_{max} - \mu mg}{m} = a$",
        r"$F_{max}$",
        r"$f_{max} = \mu mg$",
        r"$\frac{a_1 + a_2}{2}$",
    ]
    if len(sys.argv) > 1:
        tests = [sys.argv[1]]
    for t in tests:
        print(f"Input:  {t}")
        print(f"Output: {latex_to_unicode(t)}")
        print()
