# Lector y separador de CSV (sin modificar ninguna BD)
# Formato esperado (separador `;`):
# cedula;nombre;apellido1;apellido2;correo;telefono;tipo_usuario;accion

import csv
import logging
from pathlib import Path
from typing import Optional, Dict, List

DEFAULT_CSV = Path(__file__).parent / "src" / "csv" / "users.csv"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def normalize_tipo(tipo: str) -> Optional[str]:
    if not tipo:
        return None
        # Mapea variantes a 'docente' o 'padres'
    t = tipo.strip().lower()
    if t.startswith("doc") or t == "docente":
        return "docente"
    # considerar variantes singulares/plurales de padre/madre
    if t in {"padre", "madre", "padres", "madre/padre", "progenitor", "abuelo", "abuelos", "abuela", "abuelas", "encargado",
             "encargada", "encargados", "encargadas"} or "padre" in t or "madre" in t:
        return "padres"
    return None


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


def read_and_group(csv_path: Path) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    """Lee el CSV y devuelve un dict estructurado por tipo -> accion -> [rows]."""
    groups: Dict[str, Dict[str, List[Dict[str, str]]]] = {"docente": {}, "padres": {}, "skipped": {}}
        # Agrupa filas por tipo de usuario y por acción
    if not csv_path.exists():
        logging.error(f"Archivo CSV no encontrado: {csv_path}")
        return groups

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            tipo_raw = (row.get("tipo_usuario") or "").strip()
            accion_raw = (row.get("accion") or "").strip()
            tipo = normalize_tipo(tipo_raw)
            accion = normalize_accion(accion_raw)

            if tipo is None:
                groups.setdefault("skipped", {}).setdefault("tipo_desconocido", []).append({**row, "_tipo_raw": tipo_raw})
                logging.debug(f"Omitido por tipo desconocido: {tipo_raw} -> {row}")
                continue

            if accion is None:
                groups.setdefault("skipped", {}).setdefault("accion_desconocida", []).append({**row, "_accion_raw": accion_raw})
                logging.debug(f"Omitido por acción desconocida: {accion_raw} -> {row}")
                continue

            groups.setdefault(tipo, {}).setdefault(accion, []).append(row)

    return groups


def print_summary(groups: Dict[str, Dict[str, List[Dict[str, str]]]]) -> None:
    logging.info("Resumen de separación:")
        # Imprime conteos resumidos por tipo y acción
    for tipo, acciones in groups.items():
        if not acciones:
            logging.info(f"- {tipo}: 0")
            continue
        total = sum(len(v) for v in acciones.values())
        logging.info(f"- {tipo}: {total}")
        for accion, rows in acciones.items():
            logging.info(f"  - {accion}: {len(rows)}")


def print_groups(groups: Dict[str, Dict[str, List[Dict[str, str]]]], max_per_group: int = 20) -> None:
    """Imprime los registros agrupados por tipo y acción. Muestra hasta `max_per_group` filas por grupo."""
    logging.info("\nDetalle por tipo y acción:")
        # Muestra detalle de filas por grupo (máx. por grupo configurable)
    for tipo in sorted(groups.keys()):
        acciones = groups.get(tipo) or {}
        if not acciones:
            continue
        logging.info(f"\n=== Tipo: {tipo} ===")
        for accion in sorted(acciones.keys()):
            rows = acciones.get(accion, [])
            logging.info(f"-- Acción: {accion} ({len(rows)} filas)")
            to_show = rows[:max_per_group]
            for r in to_show:
                cedula = (r.get("cedula") or "").strip()
                nombre = (r.get("nombre") or "").strip()
                apellido1 = (r.get("apellido1") or "").strip()
                apellido2 = (r.get("apellido2") or "").strip()
                correo = (r.get("correo") or "").strip()
                telefono = (r.get("telefono") or "").strip()
                logging.info(f"  {cedula} | {nombre} {apellido1} {apellido2} | {correo} | {telefono}")
            if len(rows) > max_per_group:
                logging.info(f"  ... y {len(rows)-max_per_group} filas más")


def main(csv_path: Optional[str] = None) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    path = Path(csv_path) if csv_path else DEFAULT_CSV
    logging.info(f"Procesando CSV: {path}")
    groups = read_and_group(path)
    print_summary(groups)
        # Ejecuta el procesamiento y muestra resumen y detalle
    print_groups(groups)
    return groups


if __name__ == "__main__":
    main()