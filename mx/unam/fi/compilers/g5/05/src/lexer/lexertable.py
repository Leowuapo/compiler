import re

token = [
    #comentarios
    (r'//.*', None),
    (r'/\*[\s\S]*?\*/', None),

    #literales
    (r'"([^"\\]|\\.)*"', 'literal'),
    (r"'([^'\\]|\\.)'", 'literal'),

    #constantes
    (r'\d+(\.\d+)?', 'constant'),

    #operadores compuestos
    (r'==', 'operator'),
    (r'!=', 'operator'),
    (r'<=', 'operator'),
    (r'>=', 'operator'),
    (r'\+\+', 'operator'),
    (r'\-\-', 'operator'),
    (r'\+=', 'operator'),
    (r'-=', 'operator'),
    (r'\*=', 'operator'),
    (r'/=', 'operator'),
    (r'&&', 'operator'),
    (r'\|\|', 'operator'),

    #operadores simples
    (r'=', 'operator'),
    (r'\+', 'operator'),
    (r'\-', 'operator'),
    (r'\*', 'operator'),
    (r'\/', 'operator'),
    (r'%', 'operator'),
    (r'<', 'operator'),
    (r'>', 'operator'),
    (r'!', 'operator'),

    #puntuadores
    (r'\(', 'punctuation'),
    (r'\)', 'punctuation'),
    (r'\{', 'punctuation'),
    (r'\}', 'punctuation'),
    (r'\[', 'punctuation'),
    (r'\]', 'punctuation'),
    (r';', 'punctuation'),
    (r',', 'punctuation'),
    (r'\.', 'punctuation'),

    #palabras  reservadas
    (r'\bprint\b', 'keyword'),
    (r'\bprintf\b', 'keyword'),
    (r'\bif\b', 'keyword'),
    (r'\belse\b', 'keyword'),
    (r'\bwhile\b', 'keyword'),
    (r'\bfor\b', 'keyword'),
    (r'\breturn\b', 'keyword'),
    (r'\bint\b', 'keyword'),
    (r'\bfloat\b', 'keyword'),
    (r'\bdouble\b', 'keyword'),
    (r'\bchar\b', 'keyword'),
    (r'\bvoid\b', 'keyword'),
    (r'\bbreak\b', 'keyword'),
    (r'\bcontinue\b', 'keyword'),
    (r'\bmain\b', 'keyword'),
    (r'\bbool\b', 'keyword'),
    (r'\blong\b', 'keyword'),
    (r'\bswitch\b', 'keyword'),
    (r'\bcase\b', 'keyword'),
    (r'\bdefault\b', 'keyword'),
    (r'\bdo\b', 'keyword'),
    (r'\bstatic\b', 'keyword'),
    (r'\bstruct\b', 'keyword'),
    (r'\bconst\b', 'keyword'),
    (r'\bsizeof\b', 'keyword'),
    (r'\btypedef\b', 'keyword'),
    (r'\bunsigned\b', 'keyword'),
    (r'\bshort\b', 'keyword'),
    
    #identificadores
    (r'[a-zA-Z_][a-zA-Z0-9_]*', 'identifier'),
    
    #caractes especiales
    (r'#', 'special_character'),
    
    #espacios
    (r'\s+', None)
]