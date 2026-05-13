from collections import defaultdict

productions = [
    # Programa (múltiples statements)
    ("Program'", ["Program"]),
    ("Program", ["StatementList"]),
    ("StatementList", ["Statement"]),
    ("StatementList", ["StatementList", "Statement"]),
    
    # Statements
    ("Statement", ["Declaration", ";"]),
    ("Statement", ["Assignment", ";"]),
    ("Statement", ["Block"]),
    
    # Declaración con o sin inicialización, múltiples variables
    ("Declaration", ["TYPE", "DeclList"]),
    ("DeclList", ["DeclItem"]),
    ("DeclList", ["DeclList", ",", "DeclItem"]),
    ("DeclItem", ["ID"]),
    ("DeclItem", ["ID", "=", "E"]),
    
    # Asignación (variable ya declarada)
    ("Assignment", ["ID", "=", "E"]),
    
    # Bloque con ámbito
    ("Block", ["{", "StatementList", "}"]),
    ("Block", ["{", "}"]),  # bloque vacío
    
    # Expresiones aritméticas
    ("E", ["E", "+", "T"]),
    ("E", ["E", "-", "T"]),
    ("E", ["T"]),
    ("T", ["T", "*", "F"]),
    ("T", ["T", "/", "F"]),
    ("T", ["F"]),
    ("F", ["(", "E", ")"]),
    ("F", ["ID"]),
    ("F", ["CONST"]),
]

prod_num = {}
for indice, (lado_izq, lado_der) in enumerate(productions):
    prod_num[(lado_izq, tuple(lado_der))] = indice

terminales = {"TYPE", "ID", "CONST", "=", ";", "+", "-", "*", "/", "(", ")", ",", "{", "}", "$"}
no_terminales = {"Program'", "Program", "StatementList", "Statement", "Declaration", "DeclList", "DeclItem", "Assignment", "Block", "E", "T", "F"}

primeros = {s: set() for s in terminales | no_terminales}
for t in terminales:
    primeros[t].add(t)

cambio = True
while cambio:
    cambio = False
    for lado_izq, lado_der in productions:
        if lado_izq in no_terminales:
            todos_anulables = True
            for X in lado_der:
                antes = set(primeros[lado_izq])
                primeros[lado_izq] |= primeros[X] - {"ε"}
                if "ε" not in primeros[X]:
                    todos_anulables = False
                    if primeros[lado_izq] != antes:
                        cambio = True
                    break
                if "ε" in primeros[X]:
                    if primeros[lado_izq] != antes:
                        cambio = True
            if todos_anulables and "ε" not in primeros[lado_izq]:
                primeros[lado_izq].add("ε")
                cambio = True

def primero_de_cadena(simbolos):
    resultado = set()
    for X in simbolos:
        resultado |= primeros[X] - {"ε"}
        if "ε" not in primeros[X]:
            return resultado
    resultado.add("ε")
    return resultado

def cierre_lr1(items):
    conjunto = set(items)
    while True:
        nuevos = set()
        for lado_izq, lado_der, punto, la in conjunto:
            if punto < len(lado_der):
                B = lado_der[punto]
                if B in no_terminales:
                    beta = list(lado_der[punto+1:]) + [la]
                    for prod_lado_izq, prod_lado_der in productions:
                        if prod_lado_izq == B:
                            for b in primero_de_cadena(beta):
                                nuevo_item = (prod_lado_izq, tuple(prod_lado_der), 0, b)
                                if nuevo_item not in conjunto:
                                    nuevos.add(nuevo_item)
        if not nuevos:
            break
        conjunto |= nuevos
    return frozenset(conjunto)

def ir_a(items, X):
    siguientes = set()
    for lado_izq, lado_der, punto, la in items:
        if punto < len(lado_der) and lado_der[punto] == X:
            siguientes.add((lado_izq, lado_der, punto+1, la))
    if not siguientes:
        return None
    return cierre_lr1(siguientes)

def construir_estados_lr1():
    inicio = cierre_lr1({("Program'", ("Program",), 0, "$")})
    estados = [inicio]
    indice_estado = {inicio: 0}
    transiciones = {}
    i = 0
    while i < len(estados):
        items = estados[i]
        for X in terminales | no_terminales:
            siguiente = ir_a(items, X)
            if siguiente is not None:
                if siguiente not in indice_estado:
                    indice_estado[siguiente] = len(estados)
                    estados.append(siguiente)
                transiciones[(i, X)] = indice_estado[siguiente]
        i += 1
    return estados, transiciones, indice_estado

def fusionar_lalr(estados_lr1):
    nucleo_a_items = defaultdict(set)
    for items in estados_lr1:
        nucleo = frozenset((lado_izq, lado_der, punto) for lado_izq, lado_der, punto, la in items)
        nucleo_a_items[nucleo] |= items
    return list(nucleo_a_items.values())

def construir_tabla_lalr():
    estados_lr1, goto_trans, _ = construir_estados_lr1()
    estados_lalr = fusionar_lalr(estados_lr1)
    lr1_a_lalr = {}
    for i_lr1, items in enumerate(estados_lr1):
        nucleo = frozenset((lhs, rhs, punto) for lhs, rhs, punto, la in items)
        for j_lalr, lalr_items in enumerate(estados_lalr):
            if nucleo == frozenset((lhs, rhs, punto) for lhs, rhs, punto, la in lalr_items):
                lr1_a_lalr[i_lr1] = j_lalr
                break

    action = defaultdict(dict)
    go_to = defaultdict(dict)

    for i_lr1, j_lalr in lr1_a_lalr.items():
        items = estados_lr1[i_lr1]
        for lhs, rhs, punto, la in items:
            if punto < len(rhs):
                a = rhs[punto]
                if a in terminales:
                    if (i_lr1, a) in goto_trans:
                        nxt_lr1 = goto_trans[(i_lr1, a)]
                        nxt_lalr = lr1_a_lalr[nxt_lr1]
                        action[j_lalr][a] = f"S{nxt_lalr}"
            else:
                if lhs == "Program'":  # Cambiado de "S'" a "Program'"
                    action[j_lalr]["$"] = "acc"
                else:
                    num = prod_num[(lhs, rhs)]
                    action[j_lalr][la] = f"R{num}"

    for (i_lr1, X), nxt_lr1 in goto_trans.items():
        if X in no_terminales:
            j_lalr = lr1_a_lalr[i_lr1]
            nxt_lalr = lr1_a_lalr[nxt_lr1]
            go_to[j_lalr][X] = nxt_lalr

    return dict(action), dict(go_to)

tabla_action, tabla_goto = construir_tabla_lalr()

if __name__ == "__main__":
    for i, prod in enumerate(productions):
        print(f"{i}: {prod}")