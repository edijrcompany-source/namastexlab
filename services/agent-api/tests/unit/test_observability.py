"""Observabilidade — logging JSON estruturado (Etapa 18)."""

import json
import logging

from app.observability import (
    StructuredFormatter,
    get_logger,
    set_conversation_id,
    set_correlation_id,
)


class TestStructuredLogger:
    def test_json_por_linha_com_correlation_id(self) -> None:
        set_correlation_id("11111111-2222-3333-4444-555555555555")
        log = get_logger("test-obs")
        assert log.handlers[0].formatter is not None

        record = log.makeRecord("test-obs", logging.INFO, __file__, 1, "quote_ok", (), None)
        linha = StructuredFormatter().format(record)
        parsed = json.loads(linha)
        assert parsed["correlation_id"] == "11111111-2222-3333-4444-555555555555"
        assert parsed["msg"] == "quote_ok"
        assert parsed["level"] == "info"

    def test_conversation_id_no_contexto(self) -> None:
        set_conversation_id("01M1F8XGCYAPCT8Y5ESM2P36HT")
        log = get_logger("test-obs")
        record = log.makeRecord("test-obs", logging.INFO, __file__, 1, "turno", (), None)
        parsed = json.loads(StructuredFormatter().format(record))
        assert parsed["conversation_id"] == "01M1F8XGCYAPCT8Y5ESM2P36HT"

    def test_get_logger_singleton(self) -> None:
        a = get_logger("singleton-test")
        b = get_logger("singleton-test")
        assert a is b
        assert len(a.handlers) == 1

    def test_unicode_ptbr(self) -> None:
        log = get_logger("test-obs")
        record = log.makeRecord(
            "test-obs", logging.WARNING, __file__, 1, "falha na cotação", (), None
        )
        parsed = json.loads(StructuredFormatter().format(record))
        assert parsed["msg"] == "falha na cotação"
