# PENTA Compiler - documentación interna
# Salida compacta para consola: resume fases completadas, rutas de artefactos y salida de la máquina virtual.
# Los comentarios explican intención y responsabilidades; no cambian la lógica del programa.

"""Console reporting helpers for compact compiler runs."""


# Imprime una vista compacta del resultado completo de compilación.
def imprimir_resumen_ejecucion(resultado):
    """Imprime una salida compacta para ejecuciones normales."""
    source_path = resultado.get("source_path") or "<unknown>"
    output_dir = resultado.get("output_dir") or "."
    artifacts = resultado.get("artifacts") or {}
    vm_resultado = resultado.get("vm_resultado")
    vm_executed = resultado.get("vm_executed", False)

    print("Compiler run")
    print("============")
    print(f"Input: {source_path}")
    print("Status: OK")
    print()

    print("Phases:")
    print("[OK] Lexer")
    print("[OK] Parser")
    print("[OK] Semantic analysis")
    print("[OK] AST generated")
    print("[OK] TAC generated")
    print("[OK] Optimized TAC generated")
    print("[OK] Target code generated")
    print("[OK] VM execution" if vm_executed else "[SKIP] VM execution: main function not found")
    print()

    print(f"Artifacts directory: {output_dir}")
    for folder_label in ("ast_dir", "ir_dir", "target_dir"):
        path = artifacts.get(folder_label)
        if path:
            print(f"- {folder_label}: {path}")

    for label in ("ast_dot", "ast_svg", "ast_png", "tac", "tac_optimized", "target_code"):
        path = artifacts.get(label)
        if path:
            print(f"- {path}")

    if vm_executed and vm_resultado is not None:
        print()
        print("VM Output:")
        output = vm_resultado.get("output") or []
        if output:
            for line in output:
                print(line)
        else:
            print("(no output)")
        print()
        print(f"VM Return Value: {vm_resultado.get('return_value')}")
