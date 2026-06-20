# Lector y separador de CSV de estudiantes (sin modificar ninguna BD)
# Formato esperado (separador `;`):
# cedula;nombre;apellido1;apellido2;nivel;seccion;cedula_padre;accion

import csv
import logging
from pathlib import Path
from typing import Optional, Dict, List

DEFAULT_CSV = Path(__file__).parent / "src" / "csv" / "students.csv"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def normalize_accion(accion: str) -> Optional[str]:
    if not accion:
        return None
    # Normaliza la acción a insertar/update/eliminar
    a = accion.strip().lower()
    if a in {"insertar", "insert", "crear"}:
        return "insertar"
    if a in {"update", "actualizar", "modificar"}:
        return "update"
    if a in {"eliminar", "delete", "borrar"}:
        return "eliminar"
    return None


def read_and_group(csv_path: Path) -> Dict[str, List[Dict[str, str]]]:
    """Lee el CSV y devuelve un dict por accion -> [rows]."""
    # Agrupa filas por acción
    groups: Dict[str, List[Dict[str, str]]] = {"insertar": [], "update": [], "eliminar": [], "skipped": []}
    if not csv_path.exists():
        logging.error(f"Archivo CSV no encontrado: {csv_path}")
        return groups

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            accion_raw = (row.get("accion") or "").strip()
            accion = normalize_accion(accion_raw)

            if accion is None:
                groups["skipped"].append({**row, "_accion_raw": accion_raw})
                logging.debug(f"Omitido por acción desconocida: {accion_raw} -> {row}")
                continue

            groups.setdefault(accion, []).append(row)

    return groups


def print_summary(groups: Dict[str, List[Dict[str, str]]]) -> None:
    # Imprime conteos resumidos por acción
    logging.info("Resumen de separación:")
    for accion, rows in groups.items():
        logging.info(f"- {accion}: {len(rows)}")


def print_groups(groups: Dict[str, List[Dict[str, str]]], max_per_group: int = 20) -> None:
    """Imprime los registros agrupados por acción."""
    # Muestra detalle de filas por grupo
    logging.info("\nDetalle por acción:")
    for accion in ["insertar", "update", "eliminar", "skipped"]:
        rows = groups.get(accion, [])
        if not rows:
            continue
        logging.info(f"-- Acción: {accion} ({len(rows)} filas)")
        for r in rows[:max_per_group]:
            cedula = (r.get("cedula") or "").strip()
            nombre = (r.get("nombre") or "").strip()
            apellido1 = (r.get("apellido1") or "").strip()
            apellido2 = (r.get("apellido2") or "").strip()
            nivel = (r.get("nivel") or "").strip()
            seccion = (r.get("seccion") or "").strip()
            cedula_padre = (r.get("cedula_padre") or "").strip()
            logging.info(f"  {cedula} | {nombre} {apellido1} {apellido2} | {nivel} {seccion} | padre: {cedula_padre}")
        if len(rows) > max_per_group:
            logging.info(f"  ... y {len(rows)-max_per_group} filas más")


def main(csv_path: Optional[str] = None) -> Dict[str, List[Dict[str, str]]]:
    # Ejecuta el procesamiento y muestra resumen y detalle
    path = Path(csv_path) if csv_path else DEFAULT_CSV
    logging.info(f"Procesando CSV: {path}")
    groups = read_and_group(path)
    print_summary(groups)
    print_groups(groups)
    return groups


if __name__ == "__main__":
    main()
