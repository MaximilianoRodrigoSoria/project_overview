"""
Analizador de logs del dominio log_analyzer.
Implementa AnalyzerPort con parsing basado en regex.
"""

import logging
import re
from typing import Dict, List, Optional

from ..ports import AnalyzerPort
from ...config.constants import Constants


logger = logging.getLogger(__name__)


HEADER_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>ERROR|WARN|INFO)\s+\[(?P<thread>[^\]]+)\]\s+"
    r"(?P<logger>[\w\.\$]+)\s+-\s+(?P<message>.*)$"
)

EXC_RE = re.compile(
    r"^(?P<exc>[a-zA-Z0-9\._$]+Exception|Error)(?::\s*(?P<excmsg>.*))?$"
)

FRAME_RE = re.compile(
    r"^\s*at\s+(?P<where>[\w\.\$]+)\((?P<file>[^:]+):(?P<line>\d+)\)\s*$"
)


class LogAnalyzer(AnalyzerPort):
    """Analizador de logs basado en expresiones regulares"""

    def analyze(self, log_text: str) -> Dict:
        """
        Analiza logs multilinea y genera una estructura resumida.

        Args:
            log_text: Texto completo del log

        Returns:
            Diccionario con analisis estructurado
        """
        logger.debug("Analizando log de %s caracteres", len(log_text))

        lines = log_text.splitlines()
        events: List[Dict] = []

        current: Optional[Dict] = None
        stack: List[str] = []

        def flush() -> None:
            """Procesa el evento acumulado actual"""
            nonlocal current, stack
            if not current:
                return

            exc = None
            excmsg = None
            top_frame = None

            for ln in stack:
                match = EXC_RE.match(ln.strip())
                if match and not exc:
                    exc = match.group("exc")
                    excmsg = (match.group("excmsg") or "").strip() or None

                frame_match = FRAME_RE.match(ln)
                if frame_match and not top_frame:
                    top_frame = {
                        "where": frame_match.group("where"),
                        "file": frame_match.group("file"),
                        "line": int(frame_match.group("line"))
                    }

            current["exception"] = exc
            current["exception_message"] = excmsg
            current["top_frame"] = top_frame
            current["raw_block"] = "\n".join(stack).strip() or None

            events.append(current)
            current = None
            stack = []

        for ln in lines:
            header_match = HEADER_RE.match(ln)
            if header_match:
                flush()
                current = header_match.groupdict()
                stack = []
            else:
                if current is not None and ln.strip() != "":
                    stack.append(ln)

        flush()

        errors = [event for event in events if event["level"] == Constants.LEVEL_ERROR]
        warns = [event for event in events if event["level"] == Constants.LEVEL_WARN]

        groups: Dict[str, Dict] = {}
        for event in errors:
            key = self._make_error_key(event)
            group = groups.setdefault(key, {
                "count": 0,
                "exception": event.get("exception"),
                "top_frame": event.get("top_frame"),
                "logger": event.get("logger"),
                "samples": [],
                "first_ts": event.get("ts"),
                "last_ts": event.get("ts")
            })
            group["count"] += 1
            group["last_ts"] = event.get("ts")
            if len(group["samples"]) < Constants.MAX_SAMPLES_PER_GROUP:
                group["samples"].append({
                    "ts": event.get("ts"),
                    "message": event.get("message"),
                    "exception_message": event.get("exception_message")
                })

        return {
            "summary": {
                "total_events": len(events),
                "total_errors": len(errors),
                "total_warnings": len(warns)
            },
            "error_groups": list(groups.values()),
            "warnings": warns[:Constants.MAX_WARNINGS_IN_ANALYSIS],
            "events": events[:Constants.MAX_EVENTS_IN_ANALYSIS]
        }

    def _make_error_key(self, error: Dict) -> str:
        """
        Genera una clave para agrupar errores similares.

        Args:
            error: Diccionario con informacion del error

        Returns:
            Clave identificadora del grupo
        """
        exc = error.get("exception")
        top_frame = error.get("top_frame") or {}
        where = top_frame.get("where")
        line = top_frame.get("line")

        return f"{exc}|{where}|{line}"
