#!/usr/bin/env python3
"""
LaTeX 数学公式 -> Unicode 转换器
针对微信/QQ 可读性优化
"""

import re
import sys


Latex_TO_UNICODE = [
    # 希腊字母
    (r'\alpha', 'α'), (r'\beta', 'β'), (r'\gamma', 'γ'), (r'\delta', 'δ'),
    (r'\epsilon', 'ε'), (r'\zeta', 'ζ'), (r'\eta', 'η'), (r'\theta', 'θ'),
    (r'\iota', 'ι'), (r'\kappa', 'κ'), (r'\lambda', 'λ'), (r'\mu', 'μ'),
    (r'\nu', 'ν'), (r'\xi', 'ξ'), (r'\pi', 'π'), (r'\rho', 'ρ'),
    (r'\sigma', 'σ'), (r'\tau', 'τ'), (r'\upsilon', 'υ'), (r'\phi', 'φ'),
    (r'\chi', 'χ'), (r'\psi', 'ψ'), (r'\omega', 'ω'),
    (r'\Alpha', 'Α'), (r'\Beta', 'Β'), (r'\Gamma', 'Γ'), (r'\Delta', 'Δ'),
    (r'\Theta', 'Θ'), (r'\Lambda', 'Λ'), (r'\Xi', 'Ξ'), (r'\Pi', 'Π'),
    (r'\Sigma', 'Σ'), (r'\Phi', 'Φ'), (r'\Psi', 'Ψ'), (r'\Omega', 'Ω'),
    # 运算符
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
    # 集合
    (r'\mathbb{R}', 'ℝ'), (r'\mathbb{N}', 'ℕ'), (r'\mathbb{Z}', 'ℤ'),
    (r'\mathbb{Q}', 'ℚ'), (r'\mathbb{C}', 'ℂ'),
    # 常用符号
    (r'\degree', '°'), (r'\therefore', '∴'), (r'\because', '∵'),
    (r'\cdots', '⋯'), (r'\ldots', '…'), (r'\vdots', '⋮'), (r'\ddots', '⋱'),
    (r'\prime', '′'), (r'\hbar', 'ℏ'), (r'\checkmark', '✓'),
    (r'\blacksquare', '■'), (r'\square', '□'),
    # 上标数字
    (r'^2', '²'), (r'^3', '³'), (r'^4', '⁴'), (r'^5', '⁵'),
    (r'^6', '⁶'), (r'^7', '⁷'), (r'^8', '⁸'), (r'^9', '⁹'), (r'^0', '⁰'),
    # 下标数字
    ('_0', '₀'), ('_1', '₁'), ('_2', '₂'), ('_3', '₃'), ('_4', '₄'),
    ('_5', '₅'), ('_6', '₆'), ('_7', '₇'), ('_8', '₈'), ('_9', '₉'),
]


def _add_space(m):
    return m.group(1) + ' ' + m.group(2)


def convert_latex(latex_str):
    """转换单条 LaTeX 公式内容"""
    result = latex_str

    # 空格命令
    result = re.sub(r'\\quad', ' ', result)
    result = re.sub(r'\\qquad', '  ', result)
    result = re.sub(r'\\,', ' ', result)
    result = re.sub(r'\\;', ' ', result)
    result = re.sub(r'\\!', '', result)
    result = re.sub(r'\\~', ' ', result)
    result = re.sub(r'\\hspace\{[^}]*\}', ' ', result)

    # 0. \boxed{...} -> [答案: ...]
    result = re.sub(r'\\boxed\{([^{}]*)\}', r'[答案: \1]', result)

    # 1. \binom{a}{b} -> C(a,b) 和 \frac{a}{b} -> (a)/(b)
    for _ in range(6):
        result = re.sub(r'\\binom\{([^{}]*)\}\{([^{}]*)\}', r'C(\1,\2)', result)
        result = re.sub(r'\\frac\{([^{}]*)\}\{([^{}]*)\}', r'(\1)/(\2)', result)
        result = re.sub(r'\\dfrac\{([^{}]*)\}\{([^{}]*)\}', r'(\1)/(\2)', result)

    # 2. \sqrt{...}
    for _ in range(3):
        result = re.sub(r'\\sqrt\{([^{}]*)\}', r'√(\1)', result)
    result = re.sub(r'\\sqrt(\d+)', r'√\1', result)

    # 3. 处理上标下标（带括号）
    result = re.sub(r'\^\{([^}]+)\}', r'^\1', result)
    result = re.sub(r'_\{([^}]+)\}', r'_\1', result)
    result = re.sub(r'\^(\w)', r'^\1', result)
    result = re.sub(r'_(\w)', r'_\1', result)

    # 4. \text{...} 和格式命令
    result = re.sub(r'\\text\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\textbf\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\textit\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\mathsf\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\mathbf\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\mathrm\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\mathit\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\texttt\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\rm\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\bf\{([^{}]*)\}', r'\1', result)
    result = re.sub(r'\\it\{([^{}]*)\}', r'\1', result)

    # 5. 逐条替换 LaTeX 命令
    for latex, unicode_char in Latex_TO_UNICODE:
        result = result.replace(latex, unicode_char)

    # 6. 移除残留 { }
    result = re.sub(r'\{([^{}]*)\}', r'\1', result)
    # 移除残留 \command
    result = re.sub(r'\\([a-zA-Z]+)', r'\1', result)

    # 7. 智能加空格
    result = re.sub(r'(\d)([a-zA-Z])', _add_space, result)
    result = re.sub(r'([a-zA-Z])(\d)', _add_space, result)
    result = re.sub(r'(\d)(\()', _add_space, result)
    result = re.sub(r'(\))(\d)', _add_space, result)
    result = re.sub(r'\)\(', ') (', result)
    result = re.sub(r'\s+', ' ', result)

    return result.strip()


def latex_to_unicode(text):
    """将 LaTeX 公式转换为 Unicode"""
    if not text:
        return text

    result = text

    # 处理 $$...$$
    def replace_display(m):
        return '『' + convert_latex(m.group(1)) + '』'
    result = re.sub(r'\$\$(.+?)\$\$', replace_display, result, flags=re.DOTALL)

    # 处理 $...$
    def replace_inline(m):
        return convert_latex(m.group(1))
    result = re.sub(r'\$(.+?)\$', replace_inline, result, flags=re.DOTALL)

    return result


if __name__ == '__main__':
    test = sys.argv[1] if len(sys.argv) > 1 else r"$\frac{1}{2} + \alpha \times \beta \geq \frac{3}{4} + \binom{5}{2} + \boxed{x^2} + \infty + \Rightarrow$"
    print("Input: ", test)
    print("Unicode:", latex_to_unicode(test))
